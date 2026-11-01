#!/usr/bin/env python3
"""
Herramienta para publicar versiones de Capy Downloader (solo para quien mantiene el proyecto).

  python tools/release.py keygen     Crea la clave de firma (una sola vez).
  python tools/release.py build      Crea el zip firmado de la versión actual.
  python tools/release.py amo-setup  Guarda tus claves de la API de Firefox Add-ons (una sola vez).
  python tools/release.py firefox    Pide a Mozilla que firme la versión de Firefox (.xpi permanente).

La clave privada se guarda fuera del proyecto, en la carpeta .capy-downloader-signing
de tu usuario. Nunca la subas a GitHub ni la compartas: quien la tenga puede publicar
actualizaciones que todos los usuarios aceptarían.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "host"))
import ed25519  # noqa: E402

KEY_DIR = os.path.join(os.path.expanduser("~"), ".capy-downloader-signing")
PRIVATE = os.path.join(KEY_DIR, "private_key.txt")
PUBLIC = os.path.join(ROOT, "host", "update_key.txt")
INCLUDE = ["extension", "host", "docs", "build.py", "README.md", "CHANGELOG.md", "LICENSE"]
SKIP_FILES = {"yt_host.bat", "yt_host.sh"}


def keygen():
    if os.path.exists(PRIVATE):
        sys.exit(f"Ya existe una clave en {PRIVATE}. No la sobrescribo: perderla impediría publicar actualizaciones.")
    os.makedirs(KEY_DIR, exist_ok=True)
    secret = os.urandom(32)
    with open(PRIVATE, "w", encoding="utf-8") as f:
        f.write(secret.hex())
    try:
        os.chmod(PRIVATE, 0o600)
    except OSError:
        pass
    pub = ed25519.public_key(secret).hex()
    with open(PUBLIC, "w", encoding="utf-8") as f:
        f.write(pub + "\n")
    print("Clave creada.")
    print(f"  Privada (secreta, haz una copia de seguridad): {PRIVATE}")
    print(f"  Pública (va en el proyecto): {PUBLIC}")
    print(f"\nClave pública: {pub}")


def _files():
    for item in INCLUDE:
        path = os.path.join(ROOT, item)
        if os.path.isfile(path):
            yield item
        elif os.path.isdir(path):
            for base, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in sorted(files):
                    if f in SKIP_FILES or f.endswith(".pyc") or (f.startswith("com.capybara.ytdl.") and f.endswith(".json")):
                        continue
                    yield os.path.relpath(os.path.join(base, f), ROOT).replace(os.sep, "/")


def build():
    if not os.path.exists(PRIVATE):
        sys.exit("No hay clave de firma. Ejecuta primero: python tools/release.py keygen")
    with open(PRIVATE, encoding="utf-8") as f:
        secret = bytes.fromhex(f.read().strip())
    if not os.path.exists(PUBLIC) or open(PUBLIC, encoding="utf-8").read().strip() != ed25519.public_key(secret).hex():
        sys.exit("host/update_key.txt no coincide con tu clave privada. Revisa la configuración.")
    with open(os.path.join(ROOT, "extension", "manifest.base.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]

    out_dir = os.path.join(ROOT, "releases")
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, f"capy-downloader-{version}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(set(_files())):
            info = zipfile.ZipInfo(rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(ROOT, rel), "rb") as f:
                zf.writestr(info, f.read())
    with open(zip_path, "rb") as f:
        signature = ed25519.sign(secret, f.read())
    with open(zip_path + ".sig", "w", encoding="ascii") as f:
        f.write(signature.hex() + "\n")

    print(f"Versión {version} lista en la carpeta releases:")
    print(f"  {os.path.basename(zip_path)}")
    print(f"  {os.path.basename(zip_path)}.sig")
    print(f"\nCrea el release v{version} en GitHub y adjunta estos dos archivos.")


AMO_FILE = os.path.join(KEY_DIR, "amo.json")


def amo_setup():
    print("Crea tus claves en https://addons.mozilla.org/developers/addon/api/key/")
    issuer = input("JWT issuer (empieza con user:): ").strip()
    secret = input("JWT secret: ").strip()
    os.makedirs(KEY_DIR, exist_ok=True)
    with open(AMO_FILE, "w", encoding="utf-8") as f:
        json.dump({"issuer": issuer, "secret": secret}, f)
    try:
        os.chmod(AMO_FILE, 0o600)
    except OSError:
        pass
    print(f"Guardadas en {AMO_FILE} (fuera del proyecto; no las subas a GitHub).")


def firefox():
    """Firma la versión de Firefox en addons.mozilla.org como complemento no listado."""
    if not os.path.exists(AMO_FILE):
        sys.exit("Faltan tus claves de Firefox Add-ons. Ejecuta primero: python tools/release.py amo-setup")
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        sys.exit("Necesitas Node.js (incluye npx): https://nodejs.org . También puedes subir el zip de "
                 "dist/firefox a mano en addons.mozilla.org como complemento no listado.")
    with open(AMO_FILE, encoding="utf-8") as f:
        amo = json.load(f)
    with open(os.path.join(ROOT, "extension", "manifest.base.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]
    subprocess.check_call([sys.executable, os.path.join(ROOT, "build.py")])
    out_dir = os.path.join(ROOT, "releases", "firefox-tmp")
    shutil.rmtree(out_dir, ignore_errors=True)
    print("Enviando a Mozilla para firmar (puede tardar unos minutos)...")
    subprocess.check_call([npx, "--yes", "web-ext@8", "sign", "--channel", "unlisted",
                           "--source-dir", os.path.join(ROOT, "dist", "firefox"),
                           "--artifacts-dir", out_dir,
                           "--api-key", amo["issuer"], "--api-secret", amo["secret"]])
    xpis = [f for f in os.listdir(out_dir) if f.endswith(".xpi")]
    if not xpis:
        sys.exit("Mozilla no devolvió el archivo firmado. Revisa los mensajes de arriba.")
    final = os.path.join(ROOT, "releases", f"capy-downloader-firefox-{version}.xpi")
    shutil.move(os.path.join(out_dir, xpis[0]), final)
    shutil.rmtree(out_dir, ignore_errors=True)
    print(f"Listo: {final}")
    print("Adjúntalo también al release de GitHub. Para instalarlo, arrástralo a una ventana de Firefox.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "keygen":
        keygen()
    elif cmd == "build":
        build()
    elif cmd == "amo-setup":
        amo_setup()
    elif cmd == "firefox":
        firefox()
    else:
        print(__doc__)

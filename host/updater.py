"""
Actualizador de Capy Downloader.
Busca el último release en GitHub, comprueba su firma digital y, si es válida,
reemplaza los archivos de la extensión y del programa local.
"""
import io
import json
import os
import re
import runpy
import shutil
import tempfile
import urllib.request
import zipfile

import ed25519

REPO = "hamkari411/Capy-Downloader"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"

HOST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HOST_DIR)
KEY_FILE = os.path.join(HOST_DIR, "update_key.txt")
MANIFEST = os.path.join(ROOT, "extension", "manifest.base.json")

MAX_ZIP = 50 * 1024 * 1024
# Lo único que una actualización puede tocar.
ALLOWED_TOP = {"extension", "host", "docs", "build.py", "README.md", "CHANGELOG.md", "LICENSE"}
# Archivos del programa local que nunca se reemplazan: los genera install.py o es la clave.
KEEP_IN_HOST = re.compile(r"^(yt_host\.(bat|sh)|com\.capybara\.ytdl\..+\.json|update_key\.txt)$")


def current_version():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)["version"]


def vtuple(v):
    return tuple(int(n) for n in re.findall(r"\d+", str(v))[:4]) or (0,)


def public_key():
    try:
        with open(KEY_FILE, encoding="utf-8") as f:
            key = bytes.fromhex(f.read().strip())
        return key if len(key) == 32 else None
    except Exception:
        return None


def _get(url, limit):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Capy-Downloader-Updater",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError("La actualización es demasiado grande; no se descargó.")
    return data


def check():
    """Consulta el último release. Devuelve un diccionario con la información."""
    data = json.loads(_get(API_LATEST, 2 * 1024 * 1024))
    latest = str(data.get("tag_name") or "").lstrip("vV")
    assets = {a.get("name"): a.get("browser_download_url") for a in data.get("assets") or []}
    zip_name = f"capy-downloader-{latest}.zip"
    return {
        "latest": latest,
        "notes": (data.get("body") or "")[:5000],
        "page": data.get("html_url"),
        "zip_url": assets.get(zip_name),
        "sig_url": assets.get(zip_name + ".sig"),
    }


def is_available(info):
    if not info or not info.get("zip_url") or not info.get("sig_url"):
        return False
    return vtuple(info.get("latest")) > vtuple(current_version())


def _safe_names(zf):
    for name in zf.namelist():
        norm = name.replace("\\", "/")
        parts = [p for p in norm.split("/") if p]
        if (not parts or norm.startswith("/") or ".." in parts or ":" in parts[0]
                or parts[0] not in ALLOWED_TOP):
            raise RuntimeError(f"La actualización contiene una ruta no permitida: {name}")
    return zf.namelist()


def _copy_tree(src, dst, skip=None):
    for base, dirs, files in os.walk(src):
        rel = os.path.relpath(base, src)
        target = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target, exist_ok=True)
        for f in files:
            if skip and rel == "." and skip.match(f):
                continue
            shutil.copy2(os.path.join(base, f), os.path.join(target, f))


def apply(info):
    """Descarga, verifica e instala la versión indicada en info. Devuelve la versión instalada."""
    key = public_key()
    if not key:
        raise RuntimeError("Las actualizaciones automáticas no están configuradas en esta copia.")
    if not is_available(info):
        raise RuntimeError("Ya tienes la última versión.")
    for url in (info["zip_url"], info["sig_url"]):
        if not str(url).startswith(DOWNLOAD_PREFIX):
            raise RuntimeError("La actualización no viene del repositorio oficial; no se instaló.")

    blob = _get(info["zip_url"], MAX_ZIP)
    try:
        signature = bytes.fromhex(_get(info["sig_url"], 1024).decode("ascii").strip())
    except ValueError:
        signature = b""
    if not ed25519.verify(key, blob, signature):
        raise RuntimeError("La firma de la actualización no es válida, así que no se instaló nada.")

    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = _safe_names(zf)
    if "extension/manifest.base.json" not in names or "host/yt_host.py" not in names:
        raise RuntimeError("La actualización está incompleta; no se instaló.")
    new_version = json.loads(zf.read("extension/manifest.base.json"))["version"]
    if new_version != info["latest"] or vtuple(new_version) <= vtuple(current_version()):
        raise RuntimeError("La versión de la actualización no coincide; no se instaló.")

    tmp = tempfile.mkdtemp(prefix=".capy-update-", dir=ROOT)
    backup = tempfile.mkdtemp(prefix=".capy-backup-", dir=ROOT)
    try:
        zf.extractall(tmp)
        # Copia de seguridad por si algo falla a mitad.
        shutil.copytree(os.path.join(ROOT, "extension"), os.path.join(backup, "extension"))
        shutil.copytree(HOST_DIR, os.path.join(backup, "host"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        try:
            shutil.rmtree(os.path.join(ROOT, "extension"))
            shutil.copytree(os.path.join(tmp, "extension"), os.path.join(ROOT, "extension"))
            _copy_tree(os.path.join(tmp, "host"), HOST_DIR, skip=KEEP_IN_HOST)
            for item in ALLOWED_TOP - {"extension", "host"}:
                src = os.path.join(tmp, item)
                if os.path.isdir(src):
                    _copy_tree(src, os.path.join(ROOT, item))
                elif os.path.isfile(src):
                    shutil.copy2(src, os.path.join(ROOT, item))
            runpy.run_path(os.path.join(ROOT, "build.py"))["main"]()
        except Exception:
            shutil.rmtree(os.path.join(ROOT, "extension"), ignore_errors=True)
            shutil.copytree(os.path.join(backup, "extension"), os.path.join(ROOT, "extension"))
            _copy_tree(os.path.join(backup, "host"), HOST_DIR)
            runpy.run_path(os.path.join(ROOT, "build.py"))["main"]()
            raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
    return new_version

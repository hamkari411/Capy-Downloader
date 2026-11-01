#!/usr/bin/env python3
"""
Genera las versiones listas para cargar en cada navegador:
  dist/chromium -> Chrome, Brave, Edge, Opera, Vivaldi y demás navegadores basados en Chromium
  dist/brave    -> copia idéntica de dist/chromium (para quien ya la cargó con ese nombre)
  dist/firefox  -> Firefox y navegadores basados en Firefox (LibreWolf, Waterfox, Zen, Floorp...)
Así ninguno de los dos navegadores muestra avisos por campos que no entiende.
Uso: python build.py
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "extension")
DIST = os.path.join(ROOT, "dist")

# Clave PÚBLICA: solo sirve para que Brave/Chrome asignen siempre el mismo ID
# a la extensión cargada sin empaquetar. No es un secreto ni da acceso a nada.
CHROMIUM_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwOeaJPrgnUskpiS3hEzk0g3K+7GnKinmcKf2k8a2tkiosGq6OACdzzotdjc0Bgc5iy2lP3bGFRg309bLEM9F7GFqc2svTONDe0MFqZ9f/1lEaWWpqojRf1aCBM3VMra2nY+y4KVoT7gAwAZgTP7vuN0nppNL+PAfEK5WniYryXyD7HNSFG5Fmc2GnSQ7ObmWAOHqf8+WR56gow4nt6c985VHh5TfFKCxGhe9sroq2gVvzQdJz9NN1mlE/S2RYHgElcO/nq5s/cx+QC7nI03uKgZPrBY29ELwC7mYVV+AADmsMxU3KLsHMmfYQpxwB1pcX7XWYYCqc9/0/gPaDIQmUQIDAQAB"
FIREFOX_ID = "capy-ytdl@capybara"
# Firefox revisa este archivo para actualizar la versión firmada (instalación permanente).
FIREFOX_UPDATES = "https://raw.githubusercontent.com/hamkari411/Capy-Downloader/main/updates.json"


def build(target, extra):
    out = os.path.join(DIST, target)
    # Se reemplaza el contenido sin borrar la carpeta: el navegador puede tenerla cargada.
    if os.path.isdir(out):
        for name in os.listdir(out):
            path = os.path.join(out, name)
            shutil.rmtree(path, ignore_errors=True) if os.path.isdir(path) else os.remove(path)
    shutil.copytree(SRC, out, ignore=shutil.ignore_patterns("manifest.base.json"), dirs_exist_ok=True)
    with open(os.path.join(SRC, "manifest.base.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    manifest.update(extra)
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return out


def main():
    chromium_extra = {"key": CHROMIUM_KEY, "background": {"service_worker": "background.js"}}
    chromium = build("chromium", chromium_extra)
    build("brave", chromium_extra)
    with open(os.path.join(SRC, "manifest.base.json"), encoding="utf-8") as f:
        action = json.load(f)["action"]
    firefox = build("firefox", {
        "background": {"scripts": ["background.js"]},
        # Mozilla exige declarar qué datos personales recoge la extensión: Capy no recoge ninguno.
        # Esa declaración existe desde Firefox 140, por eso es la versión mínima.
        "browser_specific_settings": {"gecko": {
            "id": FIREFOX_ID, "strict_min_version": "140.0", "update_url": FIREFOX_UPDATES,
            "data_collection_permissions": {"required": ["none"]}}},
        "action": dict(action, default_area="navbar"),  # el icono aparece fijo en la barra
    })
    print("Versión para navegadores Chromium (Chrome, Brave, Edge, Opera, Vivaldi):", chromium)
    print("Versión para navegadores Firefox (Firefox, LibreWolf, Waterfox, Zen):   ", firefox)


if __name__ == "__main__":
    main()

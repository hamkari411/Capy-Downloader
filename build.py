#!/usr/bin/env python3
"""
Genera las versiones listas para cargar en cada navegador:
  dist/brave    -> Brave, Chrome, Edge (service worker + clave para ID fijo)
  dist/firefox  -> Firefox (script de fondo + ID de complemento)
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


def build(target, extra):
    out = os.path.join(DIST, target)
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(SRC, out, ignore=shutil.ignore_patterns("manifest.base.json"))
    with open(os.path.join(SRC, "manifest.base.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    manifest.update(extra)
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return out


def main():
    brave = build("brave", {
        "key": CHROMIUM_KEY,
        "background": {"service_worker": "background.js"},
    })
    firefox = build("firefox", {
        "background": {"scripts": ["background.js"]},
        "browser_specific_settings": {"gecko": {"id": FIREFOX_ID, "strict_min_version": "121.0"}},
    })
    print("Versión para Brave/Chrome:", brave)
    print("Versión para Firefox:     ", firefox)


if __name__ == "__main__":
    main()

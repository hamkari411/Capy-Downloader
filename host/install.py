#!/usr/bin/env python3
"""Registra el programa local en los navegadores basados en Chromium y en Firefox. Ejecutar: python install.py"""
import json
import os
import platform
import shutil
import subprocess
import sys

HOST = "com.capybara.ytdl"
EXTENSION_ID = "ldgecmpmlnfphpgecepjjnlkibkfkncc"  # Brave/Chrome: fijo gracias a la clave pública de build.py
FIREFOX_ID = "capy-ytdl@capybara"                  # Firefox: browser_specific_settings.gecko.id

HERE = os.path.dirname(os.path.abspath(__file__))
HOST_PY = os.path.join(HERE, "yt_host.py")
SYSTEM = platform.system()


def install_ytdlp():
    print("Instalando/actualizando yt-dlp...")
    cmd = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"]
    if subprocess.call(cmd) != 0:
        if subprocess.call(cmd + ["--user"]) != 0:
            print("No pude instalar yt-dlp automáticamente. Instálalo a mano: pip install -U yt-dlp")


def write_launcher():
    if SYSTEM == "Windows":
        path = os.path.join(HERE, "yt_host.bat")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\n"{sys.executable}" -u "{HOST_PY}" %*\r\n')
    else:
        path = os.path.join(HERE, "yt_host.sh")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nexec "{sys.executable}" -u "{HOST_PY}" "$@"\n')
        os.chmod(path, 0o755)
    return path


def write_manifests(launcher):
    """Brave/Chrome usan allowed_origins; Firefox usa allowed_extensions."""
    base = {"name": HOST, "description": "Capy Downloader (yt-dlp)",
            "path": launcher, "type": "stdio"}
    variants = {
        "chromium": dict(base, allowed_origins=[f"chrome-extension://{EXTENSION_ID}/"]),
        "firefox": dict(base, allowed_extensions=[FIREFOX_ID]),
    }
    paths = {}
    for name, data in variants.items():
        path = os.path.join(HERE, f"{HOST}.{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        paths[name] = path
    return paths


# Dónde busca cada navegador los programas locales. Chromium: Chrome, Brave, Edge, Opera,
# Vivaldi y derivados. Firefox: Firefox, LibreWolf, Waterfox, Zen, Floorp y derivados.
WINDOWS_KEYS = [
    (r"Software\Google\Chrome\NativeMessagingHosts", "chromium"),      # Chrome, Opera, Vivaldi
    (r"Software\Chromium\NativeMessagingHosts", "chromium"),
    (r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts", "chromium"),
    (r"Software\Microsoft\Edge\NativeMessagingHosts", "chromium"),
    (r"Software\Vivaldi\NativeMessagingHosts", "chromium"),
    (r"Software\Mozilla\NativeMessagingHosts", "firefox"),              # Firefox, Zen, Floorp
    (r"Software\LibreWolf\NativeMessagingHosts", "firefox"),
    (r"Software\Waterfox\NativeMessagingHosts", "firefox"),
]
MAC_DIRS = [
    ("Library/Application Support/Google/Chrome", "chromium"),
    ("Library/Application Support/Chromium", "chromium"),
    ("Library/Application Support/BraveSoftware/Brave-Browser", "chromium"),
    ("Library/Application Support/Microsoft Edge", "chromium"),
    ("Library/Application Support/Vivaldi", "chromium"),
    ("Library/Application Support/com.operasoftware.Opera", "chromium"),
    ("Library/Application Support/Mozilla", "firefox"),
    ("Library/Application Support/LibreWolf", "firefox"),
    ("Library/Application Support/Waterfox", "firefox"),
]
LINUX_DIRS = [
    (".config/google-chrome", "chromium"),
    (".config/chromium", "chromium"),
    (".config/BraveSoftware/Brave-Browser", "chromium"),
    (".config/microsoft-edge", "chromium"),
    (".config/vivaldi", "chromium"),
    (".config/opera", "chromium"),
    (".mozilla", "firefox"),
    (".librewolf", "firefox"),
    (".waterfox", "firefox"),
]


def register(paths):
    if SYSTEM == "Windows":
        import winreg
        for base, kind in WINDOWS_KEYS:
            key = base + "\\" + HOST
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, paths[kind])
        print("Registrado para los navegadores basados en Chromium y en Firefox.")
        return

    home = os.path.expanduser("~")
    targets = MAC_DIRS if SYSTEM == "Darwin" else LINUX_DIRS
    done = 0
    for rel, kind in targets:
        browser_dir = os.path.join(home, rel)
        # Solo en navegadores instalados (los dos principales siempre).
        if not os.path.isdir(browser_dir) and rel not in (targets[0][0], targets[6][0]):
            continue
        sub = "native-messaging-hosts" if kind == "firefox" and SYSTEM != "Darwin" else "NativeMessagingHosts"
        d = os.path.join(browser_dir, sub)
        os.makedirs(d, exist_ok=True)
        shutil.copy(paths[kind], os.path.join(d, HOST + ".json"))
        print("Registrado en " + d)
        done += 1
    if not done:
        print("No encontré navegadores compatibles instalados.")


def check_ffmpeg():
    if shutil.which("ffmpeg"):
        print("FFmpeg encontrado.")
        return
    print("\nATENCIÓN: no encontré FFmpeg. Lo necesitas para 720p o más y para MP3.")
    if SYSTEM == "Windows":
        print("  Instálalo con:  winget install Gyan.FFmpeg   (luego reinicia el navegador)")
    elif SYSTEM == "Darwin":
        print("  Instálalo con:  brew install ffmpeg")
    else:
        print("  Instálalo con:  sudo apt install ffmpeg")


def build_extension():
    sys.path.insert(0, os.path.dirname(HERE))
    import build
    build.main()


if __name__ == "__main__":
    install_ytdlp()
    build_extension()
    register(write_manifests(write_launcher()))
    check_ffmpeg()
    print("\nListo. Cierra por completo tu navegador y vuelve a abrirlo.")

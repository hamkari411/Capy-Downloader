#!/usr/bin/env python3
"""Registra el programa local en Brave, Chrome y Firefox. Ejecutar: python install.py"""
import json
import os
import platform
import shutil
import subprocess
import sys

HOST = "com.capybara.ytdl"
EXTENSION_ID = "ldgecmpmlnfphpgecepjjnlkibkfkncc"  # Brave/Chrome: fijo gracias a la "key" del manifest.json
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
    base = {"name": HOST, "description": "Capy YT Downloader (yt-dlp)",
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


def register(paths):
    if SYSTEM == "Windows":
        import winreg
        keys = [
            (rf"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\{HOST}", "chromium"),
            (rf"Software\Google\Chrome\NativeMessagingHosts\{HOST}", "chromium"),
            (rf"Software\Mozilla\NativeMessagingHosts\{HOST}", "firefox"),
        ]
        for key, kind in keys:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, paths[kind])
            print("Registrado en HKCU\\" + key)
        return

    home = os.path.expanduser("~")
    if SYSTEM == "Darwin":
        targets = [
            (f"{home}/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts", "chromium"),
            (f"{home}/Library/Application Support/Google/Chrome/NativeMessagingHosts", "chromium"),
            (f"{home}/Library/Application Support/Mozilla/NativeMessagingHosts", "firefox"),
        ]
    else:
        targets = [
            (f"{home}/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts", "chromium"),
            (f"{home}/.config/google-chrome/NativeMessagingHosts", "chromium"),
            (f"{home}/.mozilla/native-messaging-hosts", "firefox"),
        ]
    for d, kind in targets:
        os.makedirs(d, exist_ok=True)
        shutil.copy(paths[kind], os.path.join(d, HOST + ".json"))
        print("Registrado en " + d)


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


if __name__ == "__main__":
    install_ytdlp()
    register(write_manifests(write_launcher()))
    check_ffmpeg()
    print("\nListo. Cierra por completo Brave y/o Firefox y vuelve a abrirlos.")

#!/usr/bin/env python3
"""
Programa local de Capy YT Downloader.
Brave lo arranca vía Native Messaging y le habla por stdin/stdout
(mensajes JSON con un prefijo de 4 bytes con la longitud).
"""
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

# stdout se reserva para el protocolo; cualquier print accidental va a stderr.
_OUT = sys.stdout.buffer
_IN = sys.stdin.buffer
sys.stdout = sys.stderr

if platform.system() == "Windows":
    import msvcrt
    msvcrt.setmode(_IN.fileno(), os.O_BINARY)
    msvcrt.setmode(_OUT.fileno(), os.O_BINARY)

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

# Carpeta por defecto: Descargas, sin crear subcarpetas. El usuario puede elegir otra en Ajustes.
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Diálogo nativo para elegir carpeta. Corre en un proceso aparte para no bloquear el host.
PICKER = r"""
import sys, tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.overrideredirect(True)
root.geometry("1x1+200+200")
root.attributes("-topmost", True)
root.lift()
root.focus_force()
root.update()
path = filedialog.askdirectory(parent=root, initialdir=sys.argv[1] or None,
                               title="Elige dónde guardar las descargas", mustexist=True)
root.destroy()
sys.stdout.write(path or "")
"""
_LOCK = threading.Lock()
MAX_MESSAGE = 1024 * 1024  # 1 MB: ningún mensaje legítimo de la extensión se acerca a esto
ALLOWED_HOSTS = ("youtube.com", "youtu.be")
AUDIO_FORMATS = ("mp3", "m4a", "original")


def send(obj):
    data = json.dumps(obj).encode("utf-8")
    try:
        with _LOCK:
            _OUT.write(struct.pack("<I", len(data)))
            _OUT.write(data)
            _OUT.flush()
    except Exception:
        # Si Brave cerró la conexión, la descarga sigue igual.
        pass


def read():
    raw = _IN.read(4)
    if len(raw) < 4:
        return None
    n = struct.unpack("<I", raw)[0]
    if n > MAX_MESSAGE:
        return None
    return json.loads(_IN.read(n).decode("utf-8"))


def check_url(url):
    """Solo acepta enlaces https de YouTube; yt-dlp no debe abrir nada más."""
    try:
        u = urlparse(str(url))
    except ValueError:
        u = None
    host = (u.hostname or "").lower() if u else ""
    if not u or u.scheme != "https" or not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise RuntimeError("Solo se pueden descargar enlaces de YouTube.")
    return u.geturl()


class QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): sys.stderr.write(msg + "\n")
    def error(self, msg): sys.stderr.write(msg + "\n")


def base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "windowsfilenames": True,
        "logger": QuietLogger(),
    }


def human(n):
    if not n:
        return None
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def get_info(url):
    url = check_url(url)
    with yt_dlp.YoutubeDL(base_opts()) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []
    audio_size = 0
    for f in formats:
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            audio_size = max(audio_size, f.get("filesize") or f.get("filesize_approx") or 0)

    by_height = {}
    for f in formats:
        h = f.get("height")
        if not h or f.get("vcodec") in (None, "none"):
            continue
        fps = int(round(f.get("fps") or 30))
        size = f.get("filesize") or f.get("filesize_approx") or 0
        cur = by_height.get(h)
        if cur is None or fps > cur["fps"] or (fps == cur["fps"] and size > cur["size"]):
            by_height[h] = {
                "fps": fps,
                "size": size,
                "codec": (f.get("vcodec") or "").split(".")[0],
            }

    videos = []
    for h in sorted(by_height, reverse=True):
        v = by_height[h]
        videos.append({
            "height": h,
            "fps": v["fps"],
            "codec": v["codec"],
            "size": human(v["size"] + audio_size) if v["size"] else None,
        })

    return {
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "videos": videos,
        "ffmpeg": has_ffmpeg(),
    }


def resolve_folder(folder):
    if not folder:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        return DOWNLOAD_DIR
    folder = os.path.normpath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        raise RuntimeError(f"La carpeta de descargas no existe: {folder}. Cámbiala en Ajustes.")
    return folder


def pick_folder(initial):
    start = initial if initial and os.path.isdir(initial) else DOWNLOAD_DIR
    flags = 0x08000000 if platform.system() == "Windows" else 0  # CREATE_NO_WINDOW
    res = subprocess.run([sys.executable, "-c", PICKER, start],
                         capture_output=True, text=True, encoding="utf-8", creationflags=flags)
    if res.returncode != 0:
        raise RuntimeError("No pude abrir el selector de carpetas. Escribe la ruta a mano en Ajustes.")
    path = res.stdout.strip()
    return os.path.normpath(path) if path else None


def download(job_id, url, kind, height=None, audio="mp3", folder=None):
    target = resolve_folder(folder)
    opts = base_opts()
    opts["paths"] = {"home": target}
    last = {"t": 0}

    def progress(d):
        if d["status"] == "downloading":
            now = time.time()
            if now - last["t"] < 0.5:
                return
            last["t"] = now
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            send({
                "id": job_id, "type": "progress",
                "percent": round(done / total * 100, 1) if total else 0,
                "speed": human(d.get("speed")),
                "eta": d.get("eta"),
                "stage": "Descargando",
            })
        elif d["status"] == "finished":
            send({"id": job_id, "type": "progress", "percent": 100, "stage": "Procesando"})

    opts["progress_hooks"] = [progress]

    url = check_url(url)
    if kind not in ("video", "audio"):
        raise RuntimeError("Tipo de descarga no válido.")
    if audio not in AUDIO_FORMATS:
        audio = "mp3"
    if kind == "video":
        h = int(height)
        if not 1 <= h <= 8640:
            raise RuntimeError("Resolución no válida.")
        # Prefiere MP4 (H.264/AV1 + AAC) cuando existe; en 2K/4K YouTube solo da VP9/AV1.
        opts["format"] = f"bestvideo[height={h}]+bestaudio/best[height={h}]/best[height<={h}]"
        opts["format_sort"] = ["res", "fps", "ext:mp4:m4a"]
        opts["merge_output_format"] = "mp4"
        opts["outtmpl"] = "%(title)s [%(height)sp].%(ext)s"
    else:
        opts["format"] = "bestaudio/best"
        opts["outtmpl"] = "%(title)s.%(ext)s"
        if audio in ("mp3", "m4a"):
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio,
                "preferredquality": "320" if audio == "mp3" else "0",
            }]
            opts["format_sort"] = ["ext:m4a"] if audio == "m4a" else []

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    req = info.get("requested_downloads") or []
    path = req[0].get("filepath") if req else None
    send({"id": job_id, "type": "done", "file": path})


def is_inside(path, folder):
    try:
        return os.path.commonpath([os.path.realpath(path), os.path.realpath(folder)]) == os.path.realpath(folder)
    except ValueError:
        return False


def open_in_explorer(path, folder=None):
    """Muestra un archivo descargado o la carpeta de descargas. Nunca ejecuta archivos
    y no abre nada fuera de la carpeta de descargas elegida o de Descargas."""
    base = folder if folder and os.path.isdir(folder) else resolve_folder(None)
    if path and os.path.isfile(path) and (is_inside(path, base) or is_inside(path, DOWNLOAD_DIR)):
        target = path
    else:
        target = base
    system = platform.system()
    is_file = os.path.isfile(target)
    if system == "Windows":
        if is_file:
            subprocess.Popen(["explorer", "/select," + target])
        else:
            os.startfile(target)
    elif system == "Darwin":
        subprocess.Popen(["open", "-R", target] if is_file else ["open", target])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(target) if is_file else target])


def handle(msg):
    mid = msg.get("id")
    action = msg.get("action")
    try:
        if yt_dlp is None and action in ("info", "download"):
            raise RuntimeError("yt-dlp no está instalado. Ejecuta: python -m pip install -U yt-dlp")
        if action == "info":
            send({"id": mid, "type": "info", "data": get_info(msg["url"])})
        elif action == "download":
            download(mid, msg["url"], msg.get("kind"), msg.get("height"),
                     msg.get("audio") or "mp3", msg.get("folder"))
        elif action == "open":
            open_in_explorer(msg.get("path"), msg.get("folder"))
            send({"id": mid, "type": "ok"})
        elif action == "pick_folder":
            send({"id": mid, "type": "folder", "path": pick_folder(msg.get("initial"))})
        elif action == "default_dir":
            send({"id": mid, "type": "folder", "path": DOWNLOAD_DIR})
        else:
            raise RuntimeError(f"Acción desconocida: {action}")
    except Exception as e:
        text = str(e)
        if "ffmpeg" in text.lower() and not has_ffmpeg():
            text = "Falta FFmpeg. " + text
        send({"id": mid, "type": "error", "error": text})


def main():
    while True:
        msg = read()
        if msg is None:
            break
        threading.Thread(target=handle, args=(msg,), daemon=False).start()


if __name__ == "__main__":
    main()

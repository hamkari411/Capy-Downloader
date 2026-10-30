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

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
_LOCK = threading.Lock()


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
    return json.loads(_IN.read(n).decode("utf-8"))


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


def download(job_id, url, kind, height=None, audio="mp3"):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    opts = base_opts()
    opts["paths"] = {"home": DOWNLOAD_DIR}
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

    if kind == "video":
        h = int(height)
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


def open_in_explorer(path):
    target = path if path and os.path.exists(path) else DOWNLOAD_DIR
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
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
        if yt_dlp is None:
            raise RuntimeError("yt-dlp no está instalado. Ejecuta: python -m pip install -U yt-dlp")
        if action == "info":
            send({"id": mid, "type": "info", "data": get_info(msg["url"])})
        elif action == "download":
            download(mid, msg["url"], msg.get("kind"), msg.get("height"), msg.get("audio") or "mp3")
        elif action == "open":
            open_in_explorer(msg.get("path"))
            send({"id": mid, "type": "ok"})
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

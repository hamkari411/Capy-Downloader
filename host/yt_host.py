#!/usr/bin/env python3
"""
Programa local de Capy Downloader.
El navegador lo arranca vía Native Messaging y le habla por stdin/stdout
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

# yt-dlp se importa más tarde (ver ytdlp()), después de la actualización automática,
# para no reemplazar sus archivos mientras está en uso.
_ytdlp = None

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
ALLOWED_HOSTS = ("youtube.com", "youtu.be", "tiktok.com", "instagram.com")

# Estado del programa local (última actualización de yt-dlp y preferencia de auto-actualización).
STATE_DIR = os.path.join(os.path.expanduser("~"), ".capy-downloader")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
UPDATE_EVERY = 24 * 3600  # como mucho una vez al día
NO_WINDOW = 0x08000000 if platform.system() == "Windows" else 0  # CREATE_NO_WINDOW
_update_done = threading.Event()
_active = {"downloads": 0}
_active_lock = threading.Lock()
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


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def ytdlp_version():
    try:
        from importlib.metadata import version
        return version("yt-dlp")
    except Exception:
        return None


def pip_update():
    """Actualiza yt-dlp desde PyPI (el repositorio oficial de paquetes de Python)."""
    cmd = [sys.executable, "-m", "pip", "install", "-U", "-q", "--disable-pip-version-check", "yt-dlp"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180, creationflags=NO_WINDOW)
        if r.returncode != 0:
            r = subprocess.run(cmd + ["--user"], capture_output=True, text=True, timeout=180, creationflags=NO_WINDOW)
        return r.returncode == 0
    except Exception:
        return False


def record_update(ok):
    state = load_state()
    state["last_check"] = time.time()
    state["last_result"] = "ok" if ok else "error"
    save_state(state)


def startup_update():
    """Al arrancar, actualiza yt-dlp si toca (una vez al día y si está activado)."""
    try:
        state = load_state()
        if state.get("auto_update", True) and time.time() - state.get("last_check", 0) > UPDATE_EVERY:
            record_update(pip_update())
    except Exception:
        pass
    finally:
        _update_done.set()


def ytdlp():
    global _ytdlp
    _update_done.wait(timeout=200)
    if _ytdlp is None:
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("yt-dlp no está instalado. Ejecuta: python -m pip install -U yt-dlp")
        _ytdlp = yt_dlp
    return _ytdlp


def friendly(url, text):
    low = text.lower()
    if "instagram.com" in url and any(w in low for w in ("login", "log in", "rate-limit", "rate limit",
                                                          "empty media", "not available", "401", "403")):
        return ("Instagram no dejó descargar esta publicación sin iniciar sesión. "
                "Solo funcionan publicaciones públicas; prueba de nuevo más tarde.")
    if "tiktok.com" in url and "requested format is not available" in low:
        return NO_CLEAN
    return text


def is_watermarked(f):
    return "watermark" in (f.get("format_note") or "").lower()


NO_CLEAN = "Este video de TikTok solo está disponible con marca de agua, así que no se descarga."


def is_tiktok(url):
    host = (urlparse(url).hostname or "").lower()
    return host == "tiktok.com" or host.endswith(".tiktok.com")


def check_url(url):
    """Solo acepta enlaces https de YouTube, TikTok e Instagram; yt-dlp no debe abrir nada más."""
    try:
        u = urlparse(str(url))
    except ValueError:
        u = None
    host = (u.hostname or "").lower() if u else ""
    if not u or u.scheme != "https" or not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise RuntimeError("Solo se pueden descargar enlaces de YouTube, TikTok e Instagram.")
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
    with ytdlp().YoutubeDL(base_opts()) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []
    audio_size = 0
    for f in formats:
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            audio_size = max(audio_size, f.get("filesize") or f.get("filesize_approx") or 0)

    tiktok = is_tiktok(url)
    by_height = {}
    for f in formats:
        h = f.get("height")
        if not h or f.get("vcodec") in (None, "none"):
            continue
        if tiktok and is_watermarked(f):
            continue  # En TikTok solo se ofrecen versiones sin marca de agua.
        fps = int(round(f.get("fps") or 30))
        size = f.get("filesize") or f.get("filesize_approx") or 0
        wm = is_watermarked(f)
        cur = by_height.get(h)
        # Una versión limpia siempre gana a una con marca de agua de la misma resolución.
        better = cur is None or (cur["wm"] and not wm) or (cur["wm"] == wm and (
            fps > cur["fps"] or (fps == cur["fps"] and size > cur["size"])))
        if better:
            by_height[h] = {
                "fps": fps,
                "size": size,
                "codec": (f.get("vcodec") or "").split(".")[0],
                "wm": wm,
            }

    if tiktok and not by_height:
        raise RuntimeError(NO_CLEAN)

    videos = []
    for h in sorted(by_height, reverse=True):
        v = by_height[h]
        videos.append({
            "height": h,
            "fps": v["fps"],
            "codec": v["codec"],
            "size": human(v["size"] + audio_size) if v["size"] else None,
            "watermark": v["wm"],
        })

    return {
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "platform": info.get("extractor_key"),
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
        # En TikTok, yt-dlp ya deja al final los formatos con marca de agua.
        opts["format"] = f"bestvideo[height={h}]+bestaudio/best[height={h}]/best[height<={h}]"
        if is_tiktok(url):
            # Solo la versión sin marca de agua que entrega TikTok. Sin alternativa con marca.
            clean = "[format_note!*=?watermarked]"
            opts["format"] = f"best[height={h}]{clean}/best[height<={h}]{clean}/best{clean}"
        opts["format_sort"] = ["res", "fps", "ext:mp4:m4a"]
        opts["merge_output_format"] = "mp4"
        opts["outtmpl"] = "%(title).90B [%(height)sp].%(ext)s"
    else:
        opts["format"] = "bestaudio/best"
        opts["outtmpl"] = "%(title).90B.%(ext)s"
        if audio in ("mp3", "m4a"):
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio,
                "preferredquality": "320" if audio == "mp3" else "0",
            }]
            opts["format_sort"] = ["ext:m4a"] if audio == "m4a" else []

    with _active_lock:
        _active["downloads"] += 1
    try:
        with ytdlp().YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    finally:
        with _active_lock:
            _active["downloads"] -= 1

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
        elif action == "status":
            state = load_state()
            send({"id": mid, "type": "status", "version": ytdlp_version(),
                  "auto_update": state.get("auto_update", True), "last_check": state.get("last_check"),
                  "last_result": state.get("last_result"), "updating": not _update_done.is_set()})
        elif action == "set_auto_update":
            state = load_state()
            state["auto_update"] = bool(msg.get("value"))
            save_state(state)
            send({"id": mid, "type": "ok"})
        elif action == "update_now":
            _update_done.wait(timeout=200)
            with _active_lock:
                busy = _active["downloads"] > 0
            if busy:
                raise RuntimeError("Espera a que terminen las descargas en curso y vuelve a intentarlo.")
            ok = pip_update()
            record_update(ok)
            if not ok:
                raise RuntimeError("No se pudo actualizar yt-dlp. Revisa tu conexión a internet.")
            # restart: la extensión cierra la conexión para que la nueva versión se use desde la próxima descarga.
            send({"id": mid, "type": "updated", "version": ytdlp_version(), "restart": True})
        else:
            raise RuntimeError(f"Acción desconocida: {action}")
    except Exception as e:
        text = friendly(str(msg.get("url") or ""), str(e))
        if "ffmpeg" in text.lower() and not has_ffmpeg():
            text = "Falta FFmpeg. " + text
        send({"id": mid, "type": "error", "error": text})


def main():
    threading.Thread(target=startup_update, daemon=True).start()
    while True:
        msg = read()
        if msg is None:
            break
        threading.Thread(target=handle, args=(msg,), daemon=False).start()


if __name__ == "__main__":
    main()

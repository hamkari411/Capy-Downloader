# Notas de versión / Release notes

[Español](#español) | [English](#english)

## Español

### 1.2.0

#### Ahora se llama Capy Downloader
El proyecto nació como **Capy YT Downloader**, solo para YouTube. Desde esta versión también descarga de **TikTok** e **Instagram**, así que pasa a llamarse **Capy Downloader**: un solo descargador multiplataforma.

#### Cómo funciona con cada plataforma
- **Una sola extensión para las tres.** Al pulsar el icono, el popup reconoce de qué plataforma es el enlace de la pestaña (YouTube, TikTok o Instagram) y se lo pasa al programa local.
- **El mismo motor.** El programa local usa yt-dlp, que tiene un lector específico para cada plataforma. Con él obtiene las calidades disponibles y descarga el video. Desde 720p une el video y el audio con FFmpeg.
- **TikTok sin marca de agua.** TikTok guarda cada video en dos versiones: una limpia y otra con marca de agua. Capy Downloader solo muestra y descarga la limpia. Si un video no la tiene, no se descarga.
- **Instagram sin tu sesión.** Solo descarga reels y publicaciones públicas, sin leer tus cookies ni tu cuenta. Por eso, a veces Instagram bloquea la descarga y hay que intentarlo más tarde.
- **YouTube, igual que antes**, con todas las resoluciones disponibles.
- **Siempre al día.** Cada plataforma cambia seguido, así que el programa local actualiza yt-dlp solo una vez al día.

#### Novedades
- **Nuevo nombre: Capy Downloader.**
- **TikTok**: descarga solo la versión **sin marca de agua** que entrega TikTok. Si un video no la tiene, no se descarga.
- **Instagram**: descarga reels y publicaciones públicas, sin usar tu sesión.
- **yt-dlp se actualiza solo** una vez al día, en segundo plano y nunca durante una descarga.
- Nueva sección **Motor de descargas** en Ajustes: versión instalada, interruptor de actualización automática y botón **Actualizar ahora**.
- Nueva guía de mantenimiento en `docs/MANTENIMIENTO.md`.

#### Cambios
- El popup indica la plataforma del video.
- Los nombres de archivo largos (frecuentes en TikTok) se recortan.
- Ninguna descarga trae marca de agua: YouTube e Instagram no la añaden y en TikTok solo se usa la versión limpia.

#### Seguridad
- El programa local acepta solo enlaces `https` de YouTube, TikTok e Instagram.
- La extensión no lee cookies ni sesiones del navegador.

#### Cómo actualizar desde la 1.1
1. Descarga el repositorio de nuevo (o `git pull`).
2. Ejecuta `python install.py` en `host`.
3. Recarga la extensión desde `dist/brave` o `dist/firefox`.

### 1.1.0

#### Novedades
- **Nuevo icono** con estética cyberpunk.
- **Ajustes rápidos en el popup**: el engranaje despliega un panel para elegir la carpeta de descargas y el color sin salir del popup.
- **Página de Ajustes completa** (enlace "Más ajustes"):
  - Elige la carpeta donde se guardan las descargas con el selector de carpetas del sistema, o escribe la ruta a mano.
  - Cambia el color de la interfaz: temas Cyberpunk (predeterminado), Azul, Matrix y Ámbar, más un color de acento personalizado.
- El popup muestra en qué carpeta se va a guardar el archivo, con un acceso directo para cambiarla.
- La carpeta elegida se guarda aunque el popup se cierre al aparecer la ventana del selector.
- La barra de progreso y el contador del icono usan el color del tema.

#### Cambios
- Los archivos se guardan **directo en la carpeta elegida** (por defecto, Descargas), sin crear la subcarpeta `YouTube`.
- Ahora hay una versión de la extensión para cada navegador: `python install.py` (o `python build.py`) genera `dist/brave` y `dist/firefox`. Carga la carpeta que corresponda a tu navegador.

#### Seguridad y privacidad
- Firefox y Brave ya no muestran avisos al cargar la extensión: cada uno recibe solo los campos del manifest que entiende.
- Se reemplazó el permiso `tabs` (acceso a todas las pestañas) por `activeTab`: la extensión solo ve la pestaña en la que pulsas el icono.
- El programa local solo acepta enlaces `https` de YouTube, valida el tipo de descarga y la resolución, y rechaza mensajes anormalmente grandes.
- "Mostrar archivo" solo abre archivos dentro de tu carpeta de descargas y nunca los ejecuta.
- Los nombres de archivo se limpian de caracteres no válidos en Windows.
- El popup ya no inserta datos como HTML.

#### Cómo actualizar desde la 1.0
1. Descarga el repositorio de nuevo y reemplaza tu carpeta (o haz `git pull`).
2. Ejecuta `python install.py` dentro de `host`.
3. Quita la extensión anterior del navegador y carga `dist/brave` o `dist/firefox`.

### 1.0.0
- Primera versión: descarga de video en todas las resoluciones y de solo audio (MP3, M4A u original) en Brave y Firefox.

## English

### 1.2.0

#### It's now called Capy Downloader
The project started as **Capy YT Downloader**, for YouTube only. Starting with this version it also downloads from **TikTok** and **Instagram**, so it is now called **Capy Downloader**: a single multi-platform downloader.

#### How it works on each platform
- **One extension for all three.** When you click the icon, the popup detects which platform the link in the tab belongs to (YouTube, TikTok or Instagram) and passes it to the local program.
- **The same engine.** The local program uses yt-dlp, which has a dedicated reader for each platform. It uses it to get the available qualities and download the video. From 720p up, FFmpeg merges video and audio.
- **TikTok without watermark.** TikTok stores every video in two versions: a clean one and one with a watermark. Capy Downloader only shows and downloads the clean one. If a video doesn't have it, it is not downloaded.
- **Instagram without your session.** It only downloads public reels and posts, without reading your cookies or your account. Because of that, Instagram sometimes blocks the download and you need to try again later.
- **YouTube, same as before**, with every available resolution.
- **Always up to date.** Platforms change often, so the local program updates yt-dlp by itself once a day.

#### What's new
- **New name: Capy Downloader.**
- **TikTok**: only downloads the **watermark-free** version TikTok provides. If a video doesn't have one, it is not downloaded.
- **Instagram**: downloads public reels and posts, without using your session.
- **yt-dlp updates itself** once a day, in the background and never during a download.
- New **download engine** section in Settings: installed version, automatic update switch and an **Update now** button.
- New maintenance guide in `docs/MANTENIMIENTO.md`.

#### Changes
- The popup shows which platform the video comes from.
- Long file names (common on TikTok) are trimmed.
- No download carries a watermark: YouTube and Instagram do not add one, and on TikTok only the clean version is used.

#### Security
- The local program only accepts `https` links from YouTube, TikTok and Instagram.
- The extension does not read browser cookies or sessions.

#### How to update from 1.1
1. Download the repository again (or `git pull`).
2. Run `python install.py` inside `host`.
3. Reload the extension from `dist/brave` or `dist/firefox`.

### 1.1.0

#### What's new
- **New cyberpunk-style icon.**
- **Quick settings in the popup**: the gear icon opens a panel to choose the download folder and the color theme without leaving the popup.
- **Full settings page** ("Más ajustes" link):
  - Pick the download folder with your system's folder picker, or type the path manually.
  - Change the interface colors: Cyberpunk (default), Blue, Matrix and Amber themes, plus a custom accent color.
- The popup shows which folder the file will be saved to, with a shortcut to change it.
- The chosen folder is saved even if the popup closes when the folder picker appears.
- The progress bar and the icon badge use the theme color.

#### Changes
- Files are saved **directly into the chosen folder** (Downloads by default), without creating a `YouTube` subfolder.
- There is now a separate build for each browser: `python install.py` (or `python build.py`) generates `dist/brave` and `dist/firefox`. Load the folder that matches your browser.

#### Security and privacy
- Firefox and Brave no longer show warnings when loading the extension: each one only gets the manifest fields it understands.
- The `tabs` permission (access to all tabs) was replaced by `activeTab`: the extension only sees the tab where you click its icon.
- The local program only accepts `https` YouTube links, validates the download type and resolution, and rejects abnormally large messages.
- "Mostrar archivo" (show file) only opens files inside your download folder and never runs them.
- File names are cleaned of characters that Windows does not allow.
- The popup no longer inserts data as HTML.

#### How to update from 1.0
1. Download the repository again and replace your folder (or run `git pull`).
2. Run `python install.py` inside `host`.
3. Remove the old extension from your browser and load `dist/brave` or `dist/firefox`.

### 1.0.0
- First release: download video in every available resolution, or audio only (MP3, M4A or original), in Brave and Firefox.

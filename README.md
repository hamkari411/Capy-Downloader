# Capy YT Downloader

Extensión para **Brave** y **Firefox** que descarga videos de YouTube en cualquier resolución disponible (de 144p a 4K/8K) o solo el audio (MP3, M4A u original).

> Úsala con tu propio contenido, videos con licencia libre (Creative Commons) o material que tengas permiso de descargar. Los términos de YouTube no permiten descargar contenido ajeno sin autorización, y resubir videos de otros puede costarte strikes en tu canal.

---

## Qué hace

- Detecta el video que tienes abierto (video normal, Short o directo).
- Muestra todas las resoluciones disponibles con fps, códec y tamaño aproximado.
- Descarga el **video con audio** en MP4. Cuando existe, prefiere H.264, que funciona en cualquier editor (CapCut, Premiere, DaVinci).
- Descarga **solo el audio** en:
  - **MP3** a 320 kbps, compatible con todo.
  - **M4A** (AAC), mejor calidad por tamaño.
  - **Original**, tal cual viene de YouTube, sin convertir.
- Muestra una barra de progreso con velocidad y tiempo restante, y el porcentaje sobre el icono.
- La descarga sigue aunque cierres el popup.
- Guarda todo en `Descargas/YouTube` y tiene un botón para abrir el archivo.

## Cómo funciona

La extensión tiene dos partes que se comunican entre sí:

```
 Navegador (Brave / Firefox)                   Tu PC
+--------------------------+   Native     +--------------------------+
| extension/               |  Messaging   | host/yt_host.py          |
|  popup: lista y progreso | -----------> |  yt-dlp: lee y descarga  |
|  background: conexion    | <----------- |  FFmpeg: une y convierte |
+--------------------------+              +--------------------------+
```

**Por qué dos partes:** desde 720p, YouTube entrega el video y el audio como archivos separados, y además cifra los enlaces de descarga. Una extensión sola no puede unirlos ni descifrarlos de forma fiable. Por eso:

1. **La extensión** (`extension/`) es solo la interfaz. Lee la URL de la pestaña y muestra opciones y progreso.
2. **El programa local** (`host/yt_host.py`) usa [yt-dlp](https://github.com/yt-dlp/yt-dlp), que se mantiene al día con los cambios de YouTube, para obtener los formatos y descargar.
3. **FFmpeg** une el video con el audio y convierte a MP3/M4A.
4. Se comunican por **Native Messaging**, el mecanismo oficial de los navegadores para hablar con programas instalados en la PC. Lo único que viaja es la URL del video y la ruta del archivo final. Nada sale de tu computadora salvo la descarga desde YouTube.

### Estructura

```
capy-yt-downloader/
|-- extension/          <- lo que se carga en el navegador
|   |-- manifest.json   (sirve para Brave y Firefox)
|   |-- background.js   (conexion con el programa local)
|   `-- popup.html/css/js
`-- host/               <- el programa que corre en tu PC
    |-- yt_host.py      (descarga con yt-dlp)
    `-- install.py      (lo registra en Brave, Chrome y Firefox)
```

---

## Instalación

### Requisitos

| Programa | Para qué | Cómo instalarlo |
|---|---|---|
| Python 3.9 o más nuevo | Ejecutar el programa local | [python.org](https://www.python.org/downloads/). En Windows marca **"Add Python to PATH"** |
| FFmpeg | Unir video y audio (720p o más) y convertir a MP3 | Windows: `winget install Gyan.FFmpeg`. macOS: `brew install ffmpeg`. Linux: `sudo apt install ffmpeg` |
| Brave, o Firefox 121+ | El navegador | |

### Paso 1. Descarga el proyecto

Descarga este repositorio (botón **Code > Download ZIP**) o clónalo:

```
git clone https://github.com/hamkari411/capy-yt-downloader.git
```

Guárdalo en una carpeta fija, por ejemplo `D:\Proyectos\capy-yt-downloader`. **No la muevas después**; si lo haces, repite el paso 2.

### Paso 2. Instala el programa local

Abre una terminal en la carpeta `host` y ejecuta:

```
python install.py
```

En Windows puedes hacer clic en la barra de direcciones del explorador dentro de `host`, escribir `cmd` y pulsar Enter.

El instalador:
- instala o actualiza **yt-dlp**,
- registra el programa en **Brave, Chrome y Firefox**,
- comprueba que **FFmpeg** esté instalado.

Al final deberías ver líneas como `Registrado en ...` y `FFmpeg encontrado.`

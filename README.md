# Capy Downloader

Extensión para **Brave** y **Firefox** que descarga videos de **YouTube, TikTok e Instagram** en cualquier resolución disponible o solo el audio (MP3, M4A u original).

> Antes se llamaba **Capy YT Downloader**. Desde la versión 1.2 es multiplataforma y pasó a llamarse **Capy Downloader**. Detalles en el [CHANGELOG](CHANGELOG.md).

> Úsala con tu propio contenido, videos con licencia libre (Creative Commons) o material que tengas permiso de descargar. Los términos de YouTube, TikTok e Instagram no permiten descargar contenido ajeno sin autorización, y resubir videos de otros puede costarte sanciones en tu cuenta.

---

## Qué hace

- Detecta el video que tienes abierto:
  - **YouTube**: videos normales, Shorts y directos.
  - **TikTok**: videos públicos, siempre **sin marca de agua**.
  - **Instagram**: reels y publicaciones **públicas**. No usa tu sesión, así que Instagram a veces bloquea la descarga; ver [Problemas comunes](docs/PROBLEMAS.md).
- Muestra todas las resoluciones disponibles con fps, códec y tamaño aproximado.
- Descarga el **video con audio** en MP4. Cuando existe, prefiere H.264, que funciona en cualquier editor (CapCut, Premiere, DaVinci).
- Descarga **solo el audio** en:
  - **MP3** a 320 kbps, compatible con todo.
  - **M4A** (AAC), mejor calidad por tamaño.
  - **Original**, tal cual viene de la plataforma, sin convertir.
- **Nada sale con marca de agua**: YouTube e Instagram no la añaden y de TikTok solo se descarga la versión limpia.
- Muestra una barra de progreso con velocidad y tiempo restante, y el porcentaje sobre el icono.
- La descarga sigue aunque cierres el popup.
- Guarda el archivo directo en tu carpeta **Descargas** (sin crear subcarpetas), o en la carpeta que elijas en **Ajustes**.
- Tiene **temas de color**: Cyberpunk, Azul (claro u oscuro según el sistema), Matrix y Ámbar, más un color de acento personalizado.
- **Se mantiene al día sola**: actualiza yt-dlp automáticamente una vez al día para que las descargas no se rompan cuando las plataformas cambian.

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

**Por qué dos partes:** desde 720p, YouTube (e Instagram) entregan el video y el audio como archivos separados, y YouTube además cifra los enlaces de descarga. Una extensión sola no puede unirlos ni descifrarlos de forma fiable. Por eso:

1. **La extensión** (`extension/`) es solo la interfaz. Lee la URL de la pestaña y muestra opciones y progreso.
2. **El programa local** (`host/yt_host.py`) usa [yt-dlp](https://github.com/yt-dlp/yt-dlp), que se mantiene al día con los cambios de cada plataforma, para obtener los formatos y descargar.
3. **FFmpeg** une el video con el audio y convierte a MP3/M4A.
4. Se comunican por **Native Messaging**, el mecanismo oficial de los navegadores para hablar con programas instalados en la PC. Lo único que viaja es la URL del video y la ruta del archivo final. Nada sale de tu computadora salvo la descarga desde la plataforma y la actualización diaria de yt-dlp desde PyPI.

### Estructura

```
capy-yt-downloader/
|-- extension/          <- lo que se carga en el navegador
|   |-- manifest.base.json  (base; build.py crea el de cada navegador)
|   |-- background.js   (conexion con el programa local)
|   |-- popup.html/css/js
|   |-- options.html/css/js  (pagina de Ajustes)
|   |-- theme.css/js    (temas de color)
|   `-- icons/
|-- build.py            <- genera dist/brave y dist/firefox
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

Guárdalo en una carpeta fija, por ejemplo `C:\Herramientas\capy-yt-downloader`. **No la muevas después**; si lo haces, repite el paso 2.

### Paso 2. Instala el programa local

Abre una terminal en la carpeta `host` y ejecuta:

```
python install.py
```

En Windows puedes hacer clic en la barra de direcciones del explorador dentro de `host`, escribir `cmd` y pulsar Enter.

El instalador:
- instala o actualiza **yt-dlp**,
- registra el programa en **Brave, Chrome y Firefox**,
- prepara las carpetas `dist/brave` y `dist/firefox`, una versión lista para cada navegador,
- comprueba que **FFmpeg** esté instalado.

Al final deberías ver líneas como `Registrado en ...` y `FFmpeg encontrado.`

### Paso 3A. Cárgala en Brave

1. Abre `brave://extensions`.
2. Activa **Modo de desarrollador** (arriba a la derecha).
3. Pulsa **Cargar descomprimida** y elige la carpeta `dist/brave`.
4. Cierra Brave **por completo** y vuelve a abrirlo.
5. Pulsa el icono de rompecabezas y fija **Capy Downloader**.

### Paso 3B. Cárgala en Firefox

1. Abre `about:debugging#/runtime/this-firefox`.
2. Pulsa **Cargar complemento temporal** y elige `dist/firefox/manifest.json`.

Los complementos temporales se borran al cerrar Firefox. Para dejarla fija:
- **Opción A:** fírmala gratis en [addons.mozilla.org](https://addons.mozilla.org/developers/) como complemento **no listado**. Sube un zip con el contenido de `dist/firefox/` y Mozilla te devuelve un `.xpi` firmado que se instala de forma permanente.
- **Opción B:** usa Firefox Developer Edition, pon `xpinstall.signatures.required` en `false` desde `about:config` e instala el zip del contenido de `dist/firefox/`.

> En Linux, Firefox instalado como Snap o Flatpak no puede comunicarse con programas locales. Usa la versión `.deb` o la de mozilla.org.

### Paso 4. Úsala

1. Abre un video de YouTube, TikTok o un reel de Instagram.
2. Haz clic en el icono de la extensión.
3. Elige una resolución o un formato de audio.
4. El archivo queda en tu carpeta **Descargas**, o en la que hayas elegido.

### Ajustes

Pulsa el engranaje del popup (o el enlace **Cambiar** junto a la carpeta) y se despliega un panel para elegir la carpeta y el color. En **Más ajustes** se abre una pestaña donde además puedes:

- **Elegir la carpeta de descargas** con el botón **Elegir carpeta**, que abre el selector de carpetas de tu sistema. También puedes escribir la ruta a mano y pulsar **Guardar ruta escrita**, o volver a **Descargas**.
- **Cambiar el color de la interfaz**: elige un tema y, si quieres, un color de acento propio.
- **Ver la versión de yt-dlp**, activar o desactivar la actualización automática y **actualizar al momento**.

---

## Problemas comunes

Mira la guía en [docs/PROBLEMAS.md](docs/PROBLEMAS.md).

## Mantenimiento

Cómo se mantiene al día la extensión, cómo actualizarla y qué hacer si una plataforma deja de funcionar: [docs/MANTENIMIENTO.md](docs/MANTENIMIENTO.md).

## Novedades

Consulta [CHANGELOG.md](CHANGELOG.md).

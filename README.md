# Capy Downloader

Extensión para **cualquier navegador basado en Chromium o en Firefox** que descarga videos de **YouTube, TikTok e Instagram** en cualquier resolución disponible o solo el audio (MP3, M4A u original).

☕ **¿Te sirve Capy Downloader?** Si quieres seguir apoyando el proyecto, puedes donar lo que quieras desde aquí: **[Invítame un café en Ko-fi](https://ko-fi.com/hamkari411)**. Todo lo que llegue se usa para seguir mejorándolo, y el proyecto seguirá siendo gratis y libre.

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
- **Se actualiza a sí misma**: cuando sale una versión nueva de Capy Downloader, el popup te avisa y la instalas con un botón, sin volver a descargar nada. Antes de instalar, comprueba la firma digital del autor.

## Cómo funciona

La extensión tiene dos partes que se comunican entre sí:

```
 Navegador (Chromium / Firefox)                Tu PC
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
|-- build.py            <- genera dist/chromium y dist/firefox
|-- tools/release.py    <- firma y empaqueta versiones nuevas (para el autor)
`-- host/               <- el programa que corre en tu PC
    |-- yt_host.py      (descarga con yt-dlp)
    |-- updater.py      (busca e instala versiones nuevas firmadas)
    |-- ed25519.py      (comprobación de la firma digital)
    `-- install.py      (lo registra en los navegadores)
```

---

## Instalación

### Requisitos

| Programa | Para qué | Cómo instalarlo |
|---|---|---|
| Python 3.9 o más nuevo | Ejecutar el programa local | [python.org](https://www.python.org/downloads/). En Windows marca **"Add Python to PATH"** |
| FFmpeg | Unir video y audio (720p o más) y convertir a MP3 | Windows: `winget install Gyan.FFmpeg`. macOS: `brew install ffmpeg`. Linux: `sudo apt install ffmpeg` |
| Un navegador compatible | Usar la extensión | **Basados en Chromium:** Chrome, Brave, Edge, Opera, Vivaldi, Chromium. **Basados en Firefox (121 o más nuevo):** Firefox, LibreWolf, Waterfox, Zen, Floorp |

### Paso 1. Descarga el proyecto

Descarga este repositorio (botón **Code > Download ZIP**) o clónalo:

```
git clone https://github.com/hamkari411/Capy-Downloader.git
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
- registra el programa en los navegadores **basados en Chromium y en Firefox**,
- prepara las carpetas `dist/chromium` y `dist/firefox`, una versión lista para cada familia de navegadores,
- comprueba que **FFmpeg** esté instalado.

Al final deberías ver líneas como `Registrado en ...` y `FFmpeg encontrado.`

### Paso 3A. Navegadores basados en Chromium (Chrome, Brave, Edge, Opera, Vivaldi)

1. Abre la página de extensiones: `chrome://extensions`, `brave://extensions`, `edge://extensions`, `opera://extensions` o `vivaldi://extensions`.
2. Activa **Modo de desarrollador**.
3. Pulsa **Cargar descomprimida** (o "Cargar sin empaquetar") y elige la carpeta `dist/chromium`.
4. Cierra el navegador **por completo** y vuelve a abrirlo.
5. Fija **Capy Downloader** en la barra: icono de extensiones (pieza de rompecabezas) y chincheta.
6. Si quieres usarla en **incógnito**, entra en **Detalles** de la extensión y activa **Permitir en modo incógnito**.

En los navegadores Chromium, una extensión cargada así **se queda instalada** aunque cierres el navegador.

> Si ya la tenías cargada desde `dist/brave`, puedes seguir usándola: es la misma versión.

### Paso 3B. Navegadores basados en Firefox (Firefox, LibreWolf, Waterfox, Zen, Floorp)

**Instalación permanente (recomendada):** descarga `capy-downloader-firefox-X.Y.Z.xpi` del [último release](https://github.com/hamkari411/Capy-Downloader/releases/latest) y arrástralo a una ventana de Firefox. Es la versión firmada por Mozilla: se queda instalada aunque cierres el navegador y Firefox la actualiza solo. Al instalarla, marca **Permitir en ventanas privadas** si quieres usarla en incógnito.

**Para pruebas:** abre `about:debugging#/runtime/this-firefox`, pulsa **Cargar complemento temporal** y elige `dist/firefox/manifest.json`. Ojo: los complementos temporales **se borran al cerrar Firefox**.

Guía completa, paso a paso: [docs/FIREFOX.md](docs/FIREFOX.md).

> En Linux, Firefox instalado como Snap o Flatpak no puede comunicarse con programas locales. Usa la versión `.deb` o la de mozilla.org.

### Paso 4. Úsala

1. Abre un video de YouTube, TikTok o un reel de Instagram.
2. Haz clic en el icono de la extensión.
3. Elige una resolución o un formato de audio.
4. El archivo queda en tu carpeta **Descargas**, o en la que hayas elegido.

### Ajustes

Pulsa el engranaje del popup (o el enlace **Cambiar** junto a la carpeta) y se despliega un panel para elegir la carpeta y el color. En **Más ajustes** se abre una pestaña donde además puedes:

- **Elegir la carpeta de descargas** con el botón **Elegir carpeta**, que abre el explorador de carpetas de Capy (accesos a Descargas, Escritorio, Documentos, Videos, Música y tus discos, y botón para crear carpetas). También puedes escribir la ruta a mano y pulsar **Guardar ruta escrita**, o volver a **Descargas**.
- **Revisar si funciona en incógnito** y cómo dejar el icono fijo en la barra.
- **Cambiar el color de la interfaz**: elige un tema y, si quieres, un color de acento propio.
- **Ver la versión de yt-dlp**, activar o desactivar la actualización automática y **actualizar al momento**.
- **Buscar versiones nuevas de Capy Downloader** e instalarlas con un botón.

### Actualizaciones

Cada 12 horas, Capy Downloader revisa si hay una versión nueva en este repositorio. Si la hay, aparece una flecha **↑** sobre el icono de la extensión y el popup muestra un aviso con las novedades y un botón **Actualizar**. Al pulsarlo:

1. Descarga la versión nueva desde los releases de GitHub.
2. **Comprueba la firma digital** del autor. Si alguien alterara el archivo, la firma no coincidiría y no se instalaría nada.
3. Reemplaza los archivos de la extensión y del programa local, manteniendo tus ajustes.
4. La extensión se reinicia sola con la versión nueva.

Solo tienes que instalar a mano la 1.3.0; a partir de ahí, las siguientes se instalan desde el propio popup.

---

## Problemas comunes

Mira la guía en [docs/PROBLEMAS.md](docs/PROBLEMAS.md).

## Mantenimiento

Cómo se mantiene al día la extensión, cómo actualizarla y qué hacer si una plataforma deja de funcionar: [docs/MANTENIMIENTO.md](docs/MANTENIMIENTO.md).

## Novedades

Consulta [CHANGELOG.md](CHANGELOG.md).

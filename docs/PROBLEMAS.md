# Problemas comunes

**No encuentro el programa local**
Ejecuta `python install.py` otra vez y reinicia el navegador por completo.

**El programa local no reconoce esta extensión**
Moviste la carpeta o cambiaste el ID. Vuelve a ejecutar `python install.py`.

**Falta FFmpeg**
Instálalo (ver requisitos en el README), cierra la terminal y reinicia el navegador.

**Python no se reconoce como comando**
Reinstala Python marcando la casilla Add Python to PATH.

**La carpeta de descargas no existe**
La carpeta que elegiste en Ajustes se borró o cambió de nombre. Abre Ajustes y elige otra.

**La extensión desaparece al cerrar Firefox**
Estás usando la versión temporal de `about:debugging`. Instala la versión firmada (`capy-downloader-firefox-X.Y.Z.xpi`) del último release: se queda para siempre y se actualiza sola.

**No funciona en incógnito o en ventanas privadas**
En Chromium: Detalles de la extensión, activa "Permitir en modo incógnito". En Firefox: about:addons, Capy Downloader, "Ejecutar en ventanas privadas": Permitir. En Ajustes de Capy puedes ver si está activado. Las descargas hechas en incógnito solo aparecen en la lista cuando abres el popup desde una ventana de incógnito.

**No tienes permiso para abrir esta carpeta**
Algunas carpetas del sistema están protegidas. Elige otra, por ejemplo Descargas o Videos.

**Instagram no dejó descargar la publicación**
La extensión no usa tu sesión de Instagram por seguridad, así que solo funcionan reels y publicaciones públicas, e Instagram a veces bloquea las descargas sin sesión. Espera un rato y vuelve a intentarlo. Las cuentas privadas no se pueden descargar.

**La primera descarga del día tarda más**
Es normal: el programa local está actualizando yt-dlp. Ver [MANTENIMIENTO.md](MANTENIMIENTO.md).

**Una plataforma dejó de funcionar de repente**
Abre Ajustes y pulsa Actualizar ahora en la sección Motor de descargas.

**Este video de TikTok solo está disponible con marca de agua**
Capy Downloader solo descarga la versión limpia que entrega TikTok. En los pocos videos que no la tienen, la descarga no se hace.

**La firma de la actualización no es válida**
El archivo descargado no coincide con lo que publicó el autor, así que no se instaló nada. Vuelve a intentarlo más tarde. Si se repite, avisa en el repositorio.

**Las actualizaciones automáticas no están configuradas en esta copia**
Falta el archivo `host/update_key.txt`. Descarga de nuevo el proyecto desde GitHub.

**Uso Edge, Opera, Vivaldi u otro navegador y no encuentra el programa local**
Vuelve a ejecutar `python install.py`: registra el programa en todos los navegadores compatibles que tengas instalados. Carga la extensión desde `dist/chromium` (o `dist/firefox` si tu navegador está basado en Firefox).

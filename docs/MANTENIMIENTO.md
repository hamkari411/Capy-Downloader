# Mantenimiento

## Actualización automática de yt-dlp

yt-dlp es el motor que lee y descarga los videos. YouTube, TikTok e Instagram cambian su funcionamiento con frecuencia y yt-dlp publica versiones nuevas para adaptarse, por eso Capy Downloader lo mantiene al día solo:

- Cada vez que el navegador arranca el programa local, este revisa cuándo fue la última actualización. Si pasó más de un día, instala la última versión de yt-dlp desde PyPI, el repositorio oficial de paquetes de Python.
- Lo hace en segundo plano y sin ventanas. La primera descarga del día puede tardar unos segundos más mientras termina.
- Si no hay internet o la actualización falla, sigue usando la versión instalada y lo intenta de nuevo al día siguiente.
- Durante una descarga nunca se reemplaza yt-dlp.

Desde **Ajustes → Más ajustes → Motor de descargas** puedes:
- ver la versión instalada y cuándo se revisó por última vez,
- desactivar la actualización automática,
- pulsar **Actualizar ahora** para forzarla al momento.

La preferencia y la fecha de la última revisión se guardan en la carpeta `.capy-downloader` de tu usuario.

Si prefieres hacerlo a mano, vuelve a ejecutar `python install.py` en la carpeta `host`: también instala la última versión de yt-dlp.

## Si una plataforma deja de funcionar

1. Abre Ajustes y pulsa **Actualizar ahora**. Casi siempre esto lo arregla.
2. Si sigue fallando, es posible que yt-dlp todavía no haya publicado el arreglo. Revisa los avisos abiertos en el [repositorio de yt-dlp](https://github.com/yt-dlp/yt-dlp/issues) y vuelve a intentarlo en uno o dos días.
3. En Instagram, los bloqueos sin sesión son normales de vez en cuando; espera un rato e inténtalo otra vez.

## Actualizar Capy Downloader a una versión nueva

1. Descarga el repositorio de nuevo y reemplaza tu carpeta, o ejecuta `git pull` dentro de ella.
2. Ejecuta `python install.py` dentro de `host`.
3. Recarga la extensión: en Brave, botón de recargar en `brave://extensions`; en Firefox, quita la anterior en `about:debugging` y carga `dist/firefox/manifest.json`.
4. Cierra el navegador por completo y ábrelo de nuevo.

## Publicar una versión nueva (para quien mantiene el proyecto)

1. Cambia el número de `version` en `extension/manifest.base.json`.
2. Añade las notas en `CHANGELOG.md`, en español y en inglés.
3. Ejecuta `python build.py` y prueba `dist/brave` y `dist/firefox`.
4. Sube los cambios y crea un release en GitHub con la etiqueta `vX.Y.Z` y las notas del CHANGELOG.

Los identificadores internos (`com.capybara.ytdl` y `capy-ytdl@capybara`) no deben cambiarse: si cambian, quienes ya tienen la extensión instalada pierden la conexión con el programa local.

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

Desde la 1.3.0, Capy Downloader se actualiza solo: el popup avisa cuando hay una versión nueva y se instala con el botón **Actualizar**. También puedes buscarla en **Ajustes → Más ajustes → Actualizaciones de Capy Downloader**.

Cómo funciona por dentro:
1. Cada 12 horas, la extensión pide al programa local que consulte el último release del repositorio. Si hay una versión nueva, aparece una flecha **↑** sobre el icono.
2. Si hay una versión más nueva, descarga `capy-downloader-X.Y.Z.zip` y su firma `capy-downloader-X.Y.Z.zip.sig`.
3. Comprueba la firma con la clave pública de `host/update_key.txt`. Si no coincide, no instala nada.
4. Revisa que el zip solo contenga carpetas y archivos permitidos y que la versión sea mayor que la instalada.
5. Hace una copia de seguridad, reemplaza los archivos y regenera `dist/`. Si algo falla, restaura la copia.
6. La extensión se recarga sola.

Los archivos que genera `install.py` y la clave pública nunca se reemplazan durante una actualización.

Si prefieres hacerlo a mano: descarga el repositorio, reemplaza tu carpeta, ejecuta `python install.py` en `host` y recarga la extensión.

## Publicar una versión nueva (para quien mantiene el proyecto)

### Una sola vez: crear la clave de firma

```
python tools/release.py keygen
```

Crea dos claves:
- **Privada**, en la carpeta `.capy-downloader-signing` de tu usuario. Es la que firma las versiones. **Haz una copia de seguridad en un lugar seguro y nunca la subas a GitHub ni la compartas**: quien la tenga podría publicar actualizaciones que todos aceptarían. Si la pierdes, no podrás publicar actualizaciones automáticas.
- **Pública**, en `host/update_key.txt`. Esta sí va en el repositorio.

### Cada versión nueva

1. Cambia el número de `version` en `extension/manifest.base.json`.
2. Añade las notas en `CHANGELOG.md`, en español y en inglés.
3. Ejecuta `python build.py` y prueba `dist/chromium` y `dist/firefox`.
4. Sube los cambios a GitHub.
5. Ejecuta `python tools/release.py build`. Crea en la carpeta `releases` el zip y su firma.
6. Crea un release en GitHub con la etiqueta `vX.Y.Z`, pega las notas del CHANGELOG y **adjunta los dos archivos** (`.zip` y `.zip.sig`). Sin ellos, los usuarios no recibirán la actualización.

Te recomiendo activar la verificación en dos pasos en tu cuenta de GitHub: es la puerta de entrada de las actualizaciones de todos los usuarios.

Los identificadores internos (`com.capybara.ytdl` y `capy-ytdl@capybara`) no deben cambiarse: si cambian, quienes ya tienen la extensión instalada pierden la conexión con el programa local.

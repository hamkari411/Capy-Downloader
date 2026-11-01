# Dejar Capy Downloader instalada para siempre en Firefox

## Por qué se borra al cerrar Firefox

Lo que se carga desde `about:debugging` es un **complemento temporal**: Firefox lo borra cada vez que se cierra. El Firefox normal solo deja instalar para siempre extensiones **firmadas por Mozilla**. (Firefox Developer Edition, Nightly y ESR permiten desactivar esa comprobación, pero el Firefox normal no.)

La solución es instalar la **versión firmada** (`.xpi`). Se instala una vez, se queda al cerrar y abrir el navegador, Firefox la actualiza solo y el icono aparece fijo en la barra.

## Si solo quieres usarla

1. Descarga `capy-downloader-firefox-X.Y.Z.xpi` del [último release](https://github.com/hamkari411/Capy-Downloader/releases/latest).
2. Si tenías la versión temporal, quítala en `about:debugging` (botón **Eliminar**).
3. **Arrastra el `.xpi` a una ventana de Firefox** y pulsa **Añadir**.
4. Si la quieres usar en ventanas privadas, marca **Permitir que esta extensión se ejecute en ventanas privadas**. Si se te pasa, está en `about:addons` > Capy Downloader > **Ejecutar en ventanas privadas: Permitir**.
5. Cierra Firefox y ábrelo otra vez: la extensión sigue ahí.

El programa local se instala igual que siempre con `python install.py`; ya queda registrado para Firefox.

## Para quien publica las versiones: firmar el .xpi

La firma se hace gratis en addons.mozilla.org como complemento **no listado** (no aparece en la tienda; es para distribuirlo tú). Cada número de versión se puede firmar **una sola vez**.

### Una sola vez
1. Entra en **addons.mozilla.org/developers** con una cuenta de Firefox y acepta el acuerdo de desarrollador.

### Opción A: desde la web (sin instalar nada)
1. Ejecuta `python build.py`.
2. Abre `dist/firefox`, selecciona **todos los archivos de dentro** (no la carpeta) y comprímelos en un zip. `manifest.json` tiene que quedar en la raíz del zip.
3. En el Developer Hub pulsa **Submit a New Add-on** y elige **On your own** (por tu cuenta).
4. Sube el zip. Mozilla lo revisa de forma automática; suele tardar minutos, aunque puede llegar a 24 horas.
5. Descarga el `.xpi` firmado desde la página de la versión.

### Opción B: automática
1. Instala **Node.js** (versión LTS).
2. En el Developer Hub, entra en **Manage API Keys** y genera tus claves (JWT issuer y JWT secret).
3. Ejecuta `python tools/release.py amo-setup` y pega las claves. Se guardan fuera del proyecto; no las compartas.
4. Ejecuta `python tools/release.py firefox`. El archivo firmado queda en `releases/capy-downloader-firefox-X.Y.Z.xpi`.

### Al publicar
Adjunta el `.xpi` al release de GitHub junto con el `.zip` y el `.zip.sig`, y actualiza `updates.json` con la versión nueva: es el archivo que consultan las copias instaladas para actualizarse.

Si Mozilla dice que el ID `capy-ytdl@capybara` ya está en uso, **no lo cambies por tu cuenta**: el programa local depende de ese ID.

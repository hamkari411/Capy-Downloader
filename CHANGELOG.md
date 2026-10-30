# Notas de versión / Release notes

[Español](#español) | [English](#english)

## Español

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

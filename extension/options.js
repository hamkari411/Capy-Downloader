const $ = s => document.querySelector(s);
const dirInput = $('#dir');
const dirMsg = $('#dirMsg');

function msg(text, kind = '') {
  dirMsg.textContent = text;
  dirMsg.className = 'msg ' + kind;
}

async function saveDir(path) {
  await chrome.storage.local.set({ downloadDir: path || '' });
  dirInput.value = path || '';
  msg(path ? 'Las descargas se guardarán en esta carpeta.' : 'Las descargas se guardarán en Descargas.', 'ok');
}

function renderThemes(current) {
  const box = $('#themes');
  box.innerHTML = '';
  for (const [id, t] of Object.entries(CAPY_THEMES)) {
    const b = document.createElement('button');
    b.className = 'theme';
    b.setAttribute('role', 'radio');
    b.setAttribute('aria-checked', String(id === current));
    b.innerHTML = '<div class="sw"></div><span></span>';
    b.querySelector('span').textContent = t.name;
    for (const c of t.swatch) {
      const i = document.createElement('i');
      i.style.background = c;
      b.querySelector('.sw').appendChild(i);
    }
    b.addEventListener('click', async () => {
      await chrome.storage.local.set({ theme: id });
      renderThemes(id);
      syncAccentPicker();
    });
    box.appendChild(b);
  }
}

async function syncAccentPicker() {
  const { accent } = await chrome.storage.local.get({ accent: '' });
  // Espera a que se aplique el tema para leer su color real.
  requestAnimationFrame(() => {
    const css = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
    $('#accent').value = accent || toHex(css) || '#FF2BD6';
    $('#accentLabel').textContent = accent ? 'Color personalizado' : 'Usando el color del tema';
    chrome.storage.local.set({ accentColor: $('#accent').value });
  });
}

function toHex(c) {
  if (/^#[0-9a-f]{6}$/i.test(c)) return c;
  const m = c.match(/\d+/g);
  return m ? '#' + m.slice(0, 3).map(n => (+n).toString(16).padStart(2, '0')).join('') : '';
}

const dirPicker = capyFolderPicker($('#dirPicker'), {
  async onPick(path) {
    dirPicker.close();
    await saveDir(path);
  }
});
$('#pick').addEventListener('click', () => {
  msg('');
  dirPicker.open(dirInput.value.trim());
});

$('#saveDir').addEventListener('click', () => saveDir(dirInput.value.trim()));
$('#resetDir').addEventListener('click', () => saveDir(''));
$('#openDir').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'open', path: null }));

$('#accent').addEventListener('input', async e => {
  await chrome.storage.local.set({ accent: e.target.value, accentColor: e.target.value });
  $('#accentLabel').textContent = 'Color personalizado';
});
$('#resetAccent').addEventListener('click', async () => {
  await chrome.storage.local.set({ accent: '' });
  await capyLoadSettings();
  syncAccentPicker();
});

// ---- yt-dlp ----
const updMsg = (text, kind = '') => { $('#updMsg').textContent = text; $('#updMsg').className = 'msg ' + kind; };

async function loadEngine() {
  const r = await chrome.runtime.sendMessage({ cmd: 'host_status' });
  if (!r?.ok) { $('#ytVer').textContent = 'no disponible'; return; }
  $('#ytVer').textContent = r.data.version || 'no instalado';
  $('#autoUpdate').checked = r.data.auto_update !== false;
  $('#ytLast').textContent = r.data.updating ? '(actualizando…)'
    : r.data.last_check ? `(revisado el ${new Date(r.data.last_check * 1000).toLocaleDateString()})` : '';
}

$('#autoUpdate').addEventListener('change', async e => {
  const r = await chrome.runtime.sendMessage({ cmd: 'set_auto_update', value: e.target.checked });
  updMsg(r?.ok ? (e.target.checked ? 'Se actualizará solo una vez al día.' : 'Actualización automática desactivada.') : (r?.error || 'Error'), r?.ok ? 'ok' : 'error');
});

$('#updateNow').addEventListener('click', async () => {
  const btn = $('#updateNow');
  btn.disabled = true;
  updMsg('Actualizando yt-dlp, puede tardar un minuto…');
  const r = await chrome.runtime.sendMessage({ cmd: 'update_now' });
  btn.disabled = false;
  if (r?.ok) updMsg(`Listo: yt-dlp ${r.data.version || ''} instalado.`, 'ok');
  else updMsg(/Acción desconocida/i.test(r?.error || '')
    ? 'El programa local es de una versión anterior. Ejecuta "python install.py" otra vez y reinicia el navegador.'
    : (r?.error || 'No se pudo actualizar.'), 'error');
  loadEngine();
});

// ---- Actualizaciones de Capy Downloader ----
const capyMsg = (text, kind = '') => { $('#capyMsg').textContent = text; $('#capyMsg').className = 'msg ' + kind; };

function renderCapy(d) {
  $('#capyCur').textContent = d.current || '…';
  $('#capyAuto').checked = d.auto !== false;
  $('#capyApply').hidden = !d.available;
  $('#capyLatest').textContent = d.available ? `(hay una versión nueva: ${d.latest})`
    : d.latest ? '(es la última versión)' : '';
  if (!d.configured) capyMsg('Esta copia no tiene configurada la clave de actualizaciones.', 'error');
}

async function loadCapy(force = false) {
  const r = await chrome.runtime.sendMessage({ cmd: force ? 'capy_check_update' : 'capy_update_info' });
  if (!r?.ok) { if (force) capyMsg(r?.error || 'No se pudo consultar.', 'error'); return; }
  renderCapy(r.data);
  if (force) capyMsg(r.data.available ? `Hay una versión nueva: ${r.data.latest}.` : 'Ya tienes la última versión.', 'ok');
}

$('#capyAuto').addEventListener('change', async e => {
  const r = await chrome.runtime.sendMessage({ cmd: 'capy_set_auto', value: e.target.checked });
  capyMsg(r?.ok ? (e.target.checked ? 'Se buscarán versiones nuevas cada 12 horas.' : 'Búsqueda automática desactivada.') : (r?.error || 'Error'), r?.ok ? 'ok' : 'error');
});
$('#capyCheck').addEventListener('click', async () => {
  $('#capyCheck').disabled = true;
  capyMsg('Consultando GitHub…');
  await loadCapy(true);
  $('#capyCheck').disabled = false;
});
$('#capyApply').addEventListener('click', async () => {
  $('#capyApply').disabled = true;
  capyMsg('Descargando y comprobando la firma… La extensión se reiniciará sola al terminar.');
  const r = await chrome.runtime.sendMessage({ cmd: 'capy_apply_update' });
  if (r?.ok) capyMsg(`Versión ${r.data.version} instalada. Reiniciando…`, 'ok');
  else { $('#capyApply').disabled = false; capyMsg(r?.error || 'No se pudo actualizar.', 'error'); }
});

// ---- Navegador: incógnito y barra ----
const isFirefox = typeof browser !== 'undefined' && /firefox/i.test(navigator.userAgent);

async function loadBrowserInfo() {
  let allowed = false;
  try { allowed = await chrome.extension.isAllowedIncognitoAccess(); } catch {}
  $('#incoState').textContent = allowed ? 'activado' : 'desactivado';
  $('#incoHelp').hidden = allowed;
  $('#incoOpen').hidden = allowed || isFirefox;
  $('#incoHelp').textContent = isFirefox
    ? 'Para activarlo: abre about:addons, entra en Capy Downloader y en "Ejecutar en ventanas privadas" elige "Permitir".'
    : 'Para activarlo: pulsa el botón, busca "Permitir en modo incógnito" y actívalo.';
  $('#pinHelp').textContent = isFirefox
    ? 'En Firefox el icono aparece fijo en la barra. Si lo quitaste, pulsa el icono de extensiones (pieza de rompecabezas), busca Capy Downloader y elige "Fijar en la barra".'
    : 'Para dejar el icono fijo: pulsa el icono de extensiones (pieza de rompecabezas) en la barra y luego la chincheta junto a Capy Downloader.';
}
$('#incoOpen').addEventListener('click', () =>
  chrome.tabs.create({ url: `chrome://extensions/?id=${chrome.runtime.id}` }));

(async function init() {
  $('#ver').textContent = chrome.runtime.getManifest().version;
  const s = await capyLoadSettings();
  dirInput.value = s.downloadDir;
  if (!s.downloadDir) {
    const r = await chrome.runtime.sendMessage({ cmd: 'default_dir' });
    if (r?.ok && r.path) dirInput.placeholder = r.path;
  }
  renderThemes(s.theme);
  syncAccentPicker();
  loadEngine();
  loadCapy();
  loadBrowserInfo();
})();

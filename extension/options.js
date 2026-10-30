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

$('#pick').addEventListener('click', async () => {
  const btn = $('#pick');
  btn.disabled = true;
  msg('Se abrió una ventana para elegir la carpeta. Si no la ves, revisa la barra de tareas.');
  const r = await chrome.runtime.sendMessage({ cmd: 'pick_folder', initial: dirInput.value });
  btn.disabled = false;
  if (!r?.ok) {
    const e = String(r?.error || '');
    return msg(/Acción desconocida/i.test(e)
      ? 'El programa local es de una versión anterior. Ejecuta "python install.py" otra vez y reinicia el navegador.'
      : (e || 'No se pudo abrir el selector.'), 'error');
  }
  if (!r.path) return msg('No elegiste ninguna carpeta; se mantiene la anterior.');
  dirInput.value = r.path;
  msg('Las descargas se guardarán en esta carpeta.', 'ok');
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
})();

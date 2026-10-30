const $ = s => document.querySelector(s);
const statusEl = $('#status');
let current = null; // { url, info }

function setStatus(text, isError = false) {
  statusEl.hidden = !text;
  statusEl.textContent = text || '';
  statusEl.classList.toggle('error', isError);
}

function friendlyError(err) {
  const e = String(err || '');
  if (/native messaging host not found|not found/i.test(e))
    return 'No encuentro el programa local.\nEjecuta "python install.py" en la carpeta host y reinicia el navegador.';
  if (/forbidden|access to the specified native/i.test(e))
    return 'El programa local no reconoce esta extensión.\nVuelve a ejecutar "python install.py".';
  if (/yt-dlp no está instalado/i.test(e)) return e;
  if (/ffmpeg/i.test(e)) return 'Falta FFmpeg: es necesario para unir video y audio y para convertir a MP3.';
  if (/not a bot|sign in/i.test(e))
    return 'YouTube pidió verificación.\nActualiza yt-dlp: python -m pip install -U yt-dlp';
  if (/carpeta de descargas no existe|selector de carpetas|Acción desconocida/i.test(e))
    return /Acción desconocida/i.test(e)
      ? 'El programa local es de una versión anterior.\nEjecuta "python install.py" otra vez y reinicia el navegador.'
      : e;
  if (/^Instagram no dejó|solo está disponible con marca de agua/i.test(e)) return e;
  if (/private|unavailable/i.test(e)) return 'Este video es privado o no está disponible.';
  return e;
}

// Devuelve la plataforma del enlace o null si no es un video compatible.
function platformOf(url) {
  try {
    const u = new URL(url);
    const h = u.hostname, p = u.pathname;
    if (u.protocol !== 'https:') return null;
    if (h === 'youtu.be') return 'YouTube';
    if (/(^|\.)youtube\.com$/.test(h) && (p === '/watch' || /^\/(shorts|live)\//.test(p))) return 'YouTube';
    if (/(^|\.)tiktok\.com$/.test(h) && (/\/video\/\d+/.test(p) || /^(vm|vt)\./.test(h) || p.startsWith('/t/'))) return 'TikTok';
    if (/(^|\.)instagram\.com$/.test(h) && /^\/(reel|reels|p|tv)\//.test(p)) return 'Instagram';
  } catch {}
  return null;
}

function fmtDuration(s) {
  if (!s) return '';
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), sec = Math.floor(s % 60);
  return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(sec).padStart(2, '0');
}

function label(h) {
  return h >= 2160 ? '4K' : h >= 1440 ? '2K' : h >= 1080 ? 'Full HD' : h >= 720 ? 'HD' : '';
}

function renderInfo(info) {
  $('#video').hidden = false;
  $('#thumb').src = info.thumbnail || '';
  $('#title').textContent = info.title || 'Sin título';
  $('#meta').textContent = [current.platform, info.channel, fmtDuration(info.duration)].filter(Boolean).join(', ');

  const ul = $('#videos');
  ul.innerHTML = '';
  for (const v of info.videos) {
    const li = document.createElement('li');
    const b = document.createElement('button');
    const wmTag = current.platform === 'TikTok' ? 'sin marca de agua' : '';
    const tag = [label(v.height), v.fps > 30 ? v.fps + ' fps' : '', v.codec, wmTag].filter(Boolean).join(', ');
    const strong = document.createElement('strong');
    strong.textContent = `${Number(v.height)}p`;
    const span = document.createElement('span');
    span.textContent = tag;
    const em = document.createElement('em');
    em.textContent = v.size || '';
    b.append(strong, span, em);
    b.addEventListener('click', () => startDownload({ kind: 'video', height: v.height, label: `${v.height}p` }));
    li.appendChild(b);
    ul.appendChild(li);
  }
  $('#formats').hidden = false;
  if (!info.ffmpeg) setStatus('FFmpeg no está instalado: sin él no se pueden unir video y audio por encima de 360p ni convertir a MP3.', true);
  else setStatus('');
}

document.querySelectorAll('[data-audio]').forEach(b => {
  b.addEventListener('click', () =>
    startDownload({ kind: 'audio', audio: b.dataset.audio, label: b.dataset.audio.toUpperCase() }));
});

async function startDownload(opts) {
  if (!current) return;
  const r = await chrome.runtime.sendMessage({
    cmd: 'download', url: current.url, title: current.info.title, ...opts
  });
  if (!r?.ok) setStatus(friendlyError(r?.error), true);
}

function renderJobs(jobs) {
  const list = Object.values(jobs || {}).sort((a, b) => b.created - a.created);
  $('#jobs-wrap').hidden = list.length === 0;
  const ul = $('#jobs');
  ul.innerHTML = '';
  for (const j of list) {
    const li = document.createElement('li');
    const title = document.createElement('div');
    title.className = 'job-title';
    title.textContent = `${j.label}: ${j.title || ''}`;
    li.appendChild(title);

    const sub = document.createElement('div');
    sub.className = 'job-sub';
    if (j.status === 'running') {
      const bar = document.createElement('div');
      bar.className = 'bar';
      const fill = document.createElement('i');
      fill.style.width = `${Math.min(100, Math.max(0, Number(j.percent) || 0))}%`;
      bar.appendChild(fill);
      li.appendChild(bar);
      const parts = [j.stage, `${Math.floor(j.percent || 0)}%`, j.speed && j.speed + '/s', j.eta != null && `${j.eta} s restantes`];
      sub.textContent = parts.filter(Boolean).join(', ');
    } else if (j.status === 'done') {
      sub.classList.add('done');
      sub.textContent = 'Descargado. ';
      const open = document.createElement('button');
      open.className = 'link';
      open.textContent = 'Mostrar archivo';
      open.addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'open', path: j.file }));
      sub.appendChild(open);
    } else {
      sub.classList.add('error');
      sub.textContent = friendlyError(j.error);
    }
    li.appendChild(sub);
    ul.appendChild(li);
  }
}

// ---- Panel de ajustes desplegable ----
function togglePanel(force) {
  const panel = $('#panel');
  const open = force ?? panel.hidden;
  panel.hidden = !open;
  $('#settings').setAttribute('aria-expanded', String(open));
}

function showDir(dir) {
  const text = dir || 'Descargas';
  $('#panelDir').textContent = text;
  $('#destPath').textContent = text;
}

function panelMsg(text, isError = false) {
  const el = $('#panelMsg');
  el.textContent = text || '';
  el.classList.toggle('error', isError);
}

function renderChips(current) {
  const box = $('#themeChips');
  box.textContent = '';
  for (const [id, t] of Object.entries(CAPY_THEMES)) {
    const b = document.createElement('button');
    b.className = 'chip';
    b.title = t.name;
    b.setAttribute('role', 'radio');
    b.setAttribute('aria-label', t.name);
    b.setAttribute('aria-checked', String(id === current));
    for (const c of t.swatch) {
      const i = document.createElement('i');
      i.style.background = c;
      b.appendChild(i);
    }
    b.addEventListener('click', async () => {
      await chrome.storage.local.set({ theme: id, accent: '' });
      renderChips(id);
    });
    box.appendChild(b);
  }
}

$('#settings').addEventListener('click', () => togglePanel());
$('#changeDir').addEventListener('click', () => togglePanel(true));
$('#moreSettings').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'open_options' }));
$('#resetDir').addEventListener('click', async () => {
  await chrome.storage.local.set({ downloadDir: '' });
  panelMsg('Las descargas irán a Descargas.');
});
$('#pickDir').addEventListener('click', async () => {
  panelMsg('Se abrirá una ventana para elegir la carpeta. Si el popup se cierra, la carpeta se guarda igual.');
  const { downloadDir } = await chrome.storage.local.get({ downloadDir: '' });
  const r = await chrome.runtime.sendMessage({ cmd: 'pick_folder', initial: downloadDir });
  if (!r?.ok) panelMsg(friendlyError(r?.error), true);
  else if (!r.path) panelMsg('No elegiste ninguna carpeta.');
  else panelMsg('Carpeta guardada.');
});

chrome.storage.onChanged.addListener((c, area) => {
  if (area === 'local' && c.downloadDir) showDir(c.downloadDir.newValue);
});

$('#clear').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'clear' }));
$('#folder').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'open', path: null }));

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'session' && changes.jobs) renderJobs(changes.jobs.newValue);
});

(async function init() {
  chrome.runtime.sendMessage({ cmd: 'seen' });
  const settings = await capyLoadSettings();
  showDir(settings.downloadDir);
  renderChips(settings.theme);
  const { pickError } = await chrome.storage.local.get({ pickError: '' });
  if (pickError) { togglePanel(true); panelMsg(friendlyError(pickError), true); chrome.storage.local.set({ pickError: '' }); }
  const { jobs } = await chrome.storage.session.get('jobs');
  renderJobs(jobs);

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const platform = tab?.url ? platformOf(tab.url) : null;
  if (!platform) {
    setStatus('Abre un video de YouTube, TikTok o un reel de Instagram y vuelve a pulsar el icono.');
    return;
  }
  setStatus(`Leyendo el video de ${platform}…`);
  // Si yt-dlp se está actualizando (una vez al día), la primera lectura tarda un poco más.
  const slow = setTimeout(() => setStatus(`Leyendo el video de ${platform}…\nPuede tardar unos segundos si yt-dlp se está actualizando.`), 4000);
  const r = await chrome.runtime.sendMessage({ cmd: 'info', url: tab.url });
  clearTimeout(slow);
  if (!r?.ok) { setStatus(friendlyError(r?.error), true); return; }
  current = { url: tab.url, info: r.data, platform };
  renderInfo(r.data);
})();

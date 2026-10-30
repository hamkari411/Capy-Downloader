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
    return 'No encuentro el programa local.\nEjecuta "python install.py" en la carpeta host y reinicia Brave.';
  if (/forbidden|access to the specified native/i.test(e))
    return 'El programa local no reconoce esta extensión.\nVuelve a ejecutar "python install.py".';
  if (/yt-dlp no está instalado/i.test(e)) return e;
  if (/ffmpeg/i.test(e)) return 'Falta FFmpeg: es necesario para unir video y audio y para convertir a MP3.';
  if (/not a bot|sign in/i.test(e))
    return 'YouTube pidió verificación.\nActualiza yt-dlp: python -m pip install -U yt-dlp';
  if (/private|unavailable/i.test(e)) return 'Este video es privado o no está disponible.';
  return e;
}

function isYouTube(url) {
  try {
    const u = new URL(url);
    if (u.hostname === 'youtu.be') return true;
    if (!/(^|\.)youtube\.com$/.test(u.hostname)) return false;
    return u.pathname === '/watch' || u.pathname.startsWith('/shorts/') || u.pathname.startsWith('/live/');
  } catch { return false; }
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
  $('#meta').textContent = [info.channel, fmtDuration(info.duration)].filter(Boolean).join(', ');

  const ul = $('#videos');
  ul.innerHTML = '';
  for (const v of info.videos) {
    const li = document.createElement('li');
    const b = document.createElement('button');
    const tag = [label(v.height), v.fps > 30 ? v.fps + ' fps' : '', v.codec].filter(Boolean).join(', ');
    b.innerHTML = `<strong>${v.height}p</strong><span></span><em></em>`;
    b.querySelector('span').textContent = tag;
    b.querySelector('em').textContent = v.size || '';
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
      bar.innerHTML = `<i style="width:${j.percent || 0}%"></i>`;
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

$('#clear').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'clear' }));
$('#folder').addEventListener('click', () => chrome.runtime.sendMessage({ cmd: 'open', path: null }));

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'session' && changes.jobs) renderJobs(changes.jobs.newValue);
});

(async function init() {
  chrome.runtime.sendMessage({ cmd: 'seen' });
  const { jobs } = await chrome.storage.session.get('jobs');
  renderJobs(jobs);

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url || !isYouTube(tab.url)) {
    setStatus('Abre un video de YouTube (normal, Short o directo) y vuelve a pulsar el icono.');
    return;
  }
  const r = await chrome.runtime.sendMessage({ cmd: 'info', url: tab.url });
  if (!r?.ok) { setStatus(friendlyError(r?.error), true); return; }
  current = { url: tab.url, info: r.data };
  renderInfo(r.data);
})();

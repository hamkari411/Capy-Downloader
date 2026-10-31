// Puente entre el popup y el programa local (yt_host.py) vía Native Messaging.
const HOST = 'com.capybara.ytdl';

let port = null;
let seq = 0;
const waiters = new Map(); // respuestas puntuales (info, ping, open)
let jobs = {};             // descargas en curso / terminadas
let picking = false;       // hay un selector de carpetas abierto

chrome.storage.session.get('jobs').then(r => { jobs = r.jobs || {}; });

function save() {
  chrome.storage.session.set({ jobs });
  updateBadge();
}

let accentColor = '#FF2BD6';
chrome.storage.local.get({ accentColor: '#FF2BD6' }).then(r => { accentColor = r.accentColor; updateBadge(); });
chrome.storage.onChanged.addListener((c, area) => {
  if (area === 'local' && c.accentColor) { accentColor = c.accentColor.newValue; updateBadge(); }
});

let newVersion = '';       // versión nueva de Capy disponible (para el aviso en el icono)
chrome.storage.local.get({ newVersion: '', dismissed: '' }).then(r => {
  newVersion = r.newVersion && r.newVersion !== r.dismissed ? r.newVersion : '';
  updateBadge();
});

function updateBadge() {
  const running = Object.values(jobs).filter(j => j.status === 'running');
  if (running.length) {
    const p = Math.floor(running[running.length - 1].percent || 0);
    chrome.action.setBadgeBackgroundColor({ color: accentColor });
    chrome.action.setBadgeText({ text: p + '%' });
  } else if (Object.values(jobs).some(j => j.status === 'error' && !j.seen)) {
    chrome.action.setBadgeBackgroundColor({ color: '#D1352B' });
    chrome.action.setBadgeText({ text: '!' });
  } else if (Object.values(jobs).some(j => j.status === 'done' && !j.seen)) {
    chrome.action.setBadgeBackgroundColor({ color: '#1F8A4C' });
    chrome.action.setBadgeText({ text: '✓' });
  } else if (newVersion) {
    chrome.action.setBadgeBackgroundColor({ color: '#00A3B8' });
    chrome.action.setBadgeText({ text: '↑' });
    chrome.action.setTitle({ title: `Capy Downloader: hay una versión nueva (${newVersion})` });
  } else {
    chrome.action.setBadgeText({ text: '' });
    chrome.action.setTitle({ title: 'Descargar este video' });
  }
}

// ---- Búsqueda de versiones nuevas cada 12 horas ----
const CHECK_ALARM = 'capy-update-check';
chrome.alarms.get(CHECK_ALARM).then(a => {
  if (!a) chrome.alarms.create(CHECK_ALARM, { delayInMinutes: 1, periodInMinutes: 12 * 60 });
});
chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name !== CHECK_ALARM) return;
  request('capy_periodic').then(markUpdate).catch(() => {});
});

async function markUpdate(r) {
  const { dismissed } = await chrome.storage.local.get({ dismissed: '' });
  newVersion = r && r.available && r.latest !== dismissed ? r.latest : '';
  await chrome.storage.local.set({ newVersion: r && r.available ? r.latest : '' });
  updateBadge();
}

function connect() {
  if (port) return port;
  port = chrome.runtime.connectNative(HOST);
  port.onMessage.addListener(onHostMessage);
  port.onDisconnect.addListener(() => {
    const err = chrome.runtime.lastError?.message || 'El programa local se cerró.';
    port = null;
    for (const w of waiters.values()) w.reject(err);
    waiters.clear();
    for (const j of Object.values(jobs)) {
      if (j.status === 'running') { j.status = 'error'; j.error = err; }
    }
    save();
  });
  return port;
}

function newId(prefix) { return `${prefix}-${Date.now()}-${++seq}`; }

function request(action, payload = {}) {
  return new Promise((resolve, reject) => {
    const id = newId('rq');
    waiters.set(id, { resolve, reject });
    try {
      connect().postMessage({ id, action, ...payload });
    } catch (e) {
      waiters.delete(id);
      reject(e.message || String(e));
    }
  });
}

function onHostMessage(msg) {
  const job = jobs[msg.id];
  if (job) {
    if (msg.type === 'progress') {
      job.percent = msg.percent ?? job.percent;
      job.speed = msg.speed || null;
      job.eta = msg.eta ?? null;
      job.stage = msg.stage || job.stage;
    } else if (msg.type === 'done') {
      job.status = 'done';
      job.percent = 100;
      job.file = msg.file;
    } else if (msg.type === 'error') {
      job.status = 'error';
      job.error = msg.error;
    }
    save();
    return;
  }
  const w = waiters.get(msg.id);
  if (w) {
    waiters.delete(msg.id);
    msg.type === 'error' ? w.reject(msg.error) : w.resolve(msg);
  }
}

chrome.runtime.onMessage.addListener((m, _sender, reply) => {
  if (m.cmd === 'info') {
    request('info', { url: m.url })
      .then(r => reply({ ok: true, data: r.data }))
      .catch(e => reply({ ok: false, error: String(e) }));
    return true;
  }

  if (m.cmd === 'pick_folder' || m.cmd === 'default_dir') {
    // El fondo hace la petición y guarda el resultado él mismo: así funciona
    // aunque el popup se cierre cuando aparece la ventana del selector.
    if (m.cmd === 'pick_folder') {
      if (picking) {
        reply({ ok: false, error: 'Ya hay una ventana abierta para elegir carpeta. Búscala en la barra de tareas.' });
        return false;
      }
      picking = true;
      chrome.storage.local.set({ pickError: '' });
    }
    request(m.cmd, { initial: m.initial || '' })
      .finally(() => { if (m.cmd === 'pick_folder') picking = false; })
      .then(async r => {
        if (m.cmd === 'pick_folder' && r.path) await chrome.storage.local.set({ downloadDir: r.path });
        reply({ ok: true, path: r.path });
      })
      .catch(async e => {
        if (m.cmd === 'pick_folder') await chrome.storage.local.set({ pickError: String(e) });
        reply({ ok: false, error: String(e) });
      });
    return true;
  }

  if (m.cmd === 'host_status' || m.cmd === 'set_auto_update' || m.cmd === 'update_now') {
    const action = { host_status: 'status', set_auto_update: 'set_auto_update', update_now: 'update_now' }[m.cmd];
    request(action, { value: m.value })
      .then(r => {
        // Tras actualizar, se cierra la conexión para que la próxima descarga use la versión nueva.
        if (r.restart && port) { port.disconnect(); port = null; }
        reply({ ok: true, data: r });
      })
      .catch(e => reply({ ok: false, error: String(e) }));
    return true;
  }

  if (['capy_update_info', 'capy_check_update', 'capy_set_auto', 'capy_apply_update'].includes(m.cmd)) {
    request(m.cmd, { value: m.value })
      .then(r => {
        reply({ ok: true, data: r });
        if (m.cmd === 'capy_update_info' || m.cmd === 'capy_check_update') markUpdate(r);
        // Tras instalar una versión nueva, la extensión se recarga para usar los archivos nuevos.
        if (r.reload) setTimeout(() => chrome.runtime.reload(), 400);
      })
      .catch(e => reply({ ok: false, error: String(e) }));
    return true;
  }

  if (m.cmd === 'open_options') {
    chrome.runtime.openOptionsPage()
      .catch(() => chrome.tabs.create({ url: chrome.runtime.getURL('options.html') }));
    reply({ ok: true });
    return false;
  }

  if (m.cmd === 'download') {
    const id = newId('dl');
    jobs[id] = {
      id, title: m.title, label: m.label, status: 'running',
      percent: 0, stage: 'Iniciando', created: Date.now()
    };
    save();
    chrome.storage.local.get({ downloadDir: '' }).then(({ downloadDir }) => {
      try {
        connect().postMessage({
          id, action: 'download', url: m.url,
          kind: m.kind, height: m.height, audio: m.audio, folder: downloadDir
        });
        reply({ ok: true, id });
      } catch (e) {
        jobs[id].status = 'error';
        jobs[id].error = e.message || String(e);
        save();
        reply({ ok: false, error: jobs[id].error });
      }
    });
    return true;
  }

  if (m.cmd === 'open') {
    chrome.storage.local.get({ downloadDir: '' }).then(({ downloadDir }) =>
      request('open', { path: m.path, folder: downloadDir }).catch(() => {}));
    reply({ ok: true });
    return false;
  }

  if (m.cmd === 'seen') {
    for (const j of Object.values(jobs)) j.seen = true;
    save();
    reply({ ok: true });
    return false;
  }

  if (m.cmd === 'clear') {
    for (const [k, j] of Object.entries(jobs)) if (j.status !== 'running') delete jobs[k];
    save();
    reply({ ok: true });
    return false;
  }
});

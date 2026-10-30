// Puente entre el popup y el programa local (yt_host.py) vía Native Messaging.
const HOST = 'com.capybara.ytdl';

let port = null;
let seq = 0;
const waiters = new Map(); // respuestas puntuales (info, ping, open)
let jobs = {};             // descargas en curso / terminadas

chrome.storage.session.get('jobs').then(r => { jobs = r.jobs || {}; });

function save() {
  chrome.storage.session.set({ jobs });
  updateBadge();
}

function updateBadge() {
  const running = Object.values(jobs).filter(j => j.status === 'running');
  if (running.length) {
    const p = Math.floor(running[running.length - 1].percent || 0);
    chrome.action.setBadgeBackgroundColor({ color: '#2F6FEB' });
    chrome.action.setBadgeText({ text: p + '%' });
  } else if (Object.values(jobs).some(j => j.status === 'error' && !j.seen)) {
    chrome.action.setBadgeBackgroundColor({ color: '#D1352B' });
    chrome.action.setBadgeText({ text: '!' });
  } else if (Object.values(jobs).some(j => j.status === 'done' && !j.seen)) {
    chrome.action.setBadgeBackgroundColor({ color: '#1F8A4C' });
    chrome.action.setBadgeText({ text: '✓' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
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

  if (m.cmd === 'download') {
    const id = newId('dl');
    jobs[id] = {
      id, title: m.title, label: m.label, status: 'running',
      percent: 0, stage: 'Iniciando', created: Date.now()
    };
    save();
    try {
      connect().postMessage({
        id, action: 'download', url: m.url,
        kind: m.kind, height: m.height, audio: m.audio
      });
      reply({ ok: true, id });
    } catch (e) {
      jobs[id].status = 'error';
      jobs[id].error = e.message || String(e);
      save();
      reply({ ok: false, error: jobs[id].error });
    }
    return true;
  }

  if (m.cmd === 'open') {
    request('open', { path: m.path }).catch(() => {});
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

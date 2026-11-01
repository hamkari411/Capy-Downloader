// Explorador de carpetas propio de Capy Downloader. Reemplaza la ventana del sistema,
// que en Windows a veces tardaba o se abría detrás del navegador. Es instantáneo,
// siempre aparece dentro de la extensión y funciona igual en Chromium y en Firefox.
function capyFolderPicker(root, { onPick }) {
  root.classList.add('fp');
  root.innerHTML = `
    <div class="fp-places"></div>
    <div class="fp-bar">
      <button type="button" class="fp-up" title="Carpeta superior" aria-label="Carpeta superior">↑</button>
      <span class="fp-path"></span>
    </div>
    <ul class="fp-list" role="listbox" aria-label="Carpetas"></ul>
    <div class="fp-new">
      <input type="text" class="fp-name" placeholder="Nueva carpeta" aria-label="Nombre de la carpeta nueva">
      <button type="button" class="fp-create">Crear</button>
    </div>
    <div class="fp-actions">
      <button type="button" class="fp-use">Usar esta carpeta</button>
      <button type="button" class="fp-cancel">Cancelar</button>
    </div>
    <p class="fp-msg" role="status"></p>`;
  const q = s => root.querySelector(s);
  let current = null;

  const msg = (text, isError = false) => {
    q('.fp-msg').textContent = text || '';
    q('.fp-msg').classList.toggle('error', isError);
  };

  function chip(item) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'fp-chip';
    b.textContent = item.name;
    b.title = item.path;
    b.addEventListener('click', () => go(item.path));
    return b;
  }

  async function go(path) {
    msg('');
    const r = await chrome.runtime.sendMessage({ cmd: 'list_dirs', path: path || '' });
    if (!r?.ok) return msg(r?.error || 'No se pudo leer la carpeta.', true);
    const d = r.data;
    current = d.path;
    // Aislamiento izquierda-a-derecha: la ruta se recorta por la izquierda sin mover las barras.
    q('.fp-path').textContent = '\u2066' + d.path + '\u2069';
    q('.fp-path').title = d.path;
    q('.fp-up').disabled = !d.parent;
    q('.fp-up').onclick = () => d.parent && go(d.parent);

    const places = q('.fp-places');
    places.textContent = '';
    [...d.places, ...d.drives].forEach(p => places.appendChild(chip(p)));

    const list = q('.fp-list');
    list.textContent = '';
    if (!d.dirs.length) {
      const li = document.createElement('li');
      li.className = 'fp-empty';
      li.textContent = 'No hay subcarpetas aquí.';
      list.appendChild(li);
    }
    for (const dir of d.dirs) {
      const li = document.createElement('li');
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'fp-item';
      b.textContent = '📁 ' + dir.name;
      b.addEventListener('click', () => go(dir.path));
      li.appendChild(b);
      list.appendChild(li);
    }
    list.scrollTop = 0;
  }

  q('.fp-use').addEventListener('click', () => current && onPick(current));
  q('.fp-cancel').addEventListener('click', () => { root.hidden = true; });
  q('.fp-create').addEventListener('click', async () => {
    const name = q('.fp-name').value;
    const r = await chrome.runtime.sendMessage({ cmd: 'make_dir', path: current, name });
    if (!r?.ok) return msg(r?.error || 'No se pudo crear la carpeta.', true);
    q('.fp-name').value = '';
    await go(r.path);
    msg('Carpeta creada.');
  });
  q('.fp-name').addEventListener('keydown', e => { if (e.key === 'Enter') q('.fp-create').click(); });

  return {
    open(path) { root.hidden = false; go(path); },
    close() { root.hidden = true; }
  };
}

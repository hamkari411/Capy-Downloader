// Aplica el tema guardado en Ajustes a la página actual (popup u opciones).
const CAPY_THEMES = {
  cyber:  { name: 'Cyberpunk', swatch: ['#FF2BD6', '#00E5FF'] },
  azul:   { name: 'Azul (claro u oscuro según el sistema)', swatch: ['#2F6FEB', '#EEF1F5'] },
  matrix: { name: 'Matrix', swatch: ['#39FF7A', '#050D07'] },
  ambar:  { name: 'Ámbar', swatch: ['#FFB020', '#140E05'] }
};
const CAPY_DEFAULTS = { theme: 'cyber', accent: '', downloadDir: '' };

function capyApplyTheme(s) {
  const root = document.documentElement;
  root.dataset.theme = CAPY_THEMES[s.theme] ? s.theme : 'cyber';
  if (s.accent) {
    root.style.setProperty('--accent', s.accent);
    root.style.setProperty('--accent2', s.accent);
  } else {
    root.style.removeProperty('--accent');
    root.style.removeProperty('--accent2');
  }
}

async function capyLoadSettings() {
  const s = await chrome.storage.local.get(CAPY_DEFAULTS);
  capyApplyTheme(s);
  return s;
}

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && (changes.theme || changes.accent)) capyLoadSettings();
});

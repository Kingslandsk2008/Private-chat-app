(function() {
'use strict';

const state = window.KAJUU_STATE || {};
const settings = window.KAJUU_SETTINGS || {
  apiKey: '',
  style: 'balanced',
  fontSize: 15,
};

function showAlert(message, isError) {
  const toast = document.getElementById('alertToast');
  const msg = document.getElementById('alertMessage');
  msg.textContent = message;
  toast.classList.add('show');
  if (isError) toast.style.borderColor = '#ef4444';
  else toast.style.borderColor = 'var(--color-accent)';
  clearTimeout(window._alertTimer);
  window._alertTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

const settingsBtn = document.getElementById('settingsBtn');
const settingsPanel = document.getElementById('settingsPanel');
const settingsClose = document.getElementById('settingsClose');
const overlay = document.getElementById('overlay');
const apiKeyInput = document.getElementById('apiKeyInput');
const styleSelect = document.getElementById('styleSelect');
const fontSlider = document.getElementById('fontSlider');
const fontSizeVal = document.getElementById('fontSizeVal');
const clearDataBtn = document.getElementById('clearDataBtn');
const toggleApi = document.getElementById('toggleApiVisibility');

function loadSettings() {
  try {
    const stored = localStorage.getItem('kajuu_settings');
    if (stored) {
      const s = JSON.parse(stored);
      Object.assign(settings, s);
    }
    const key = localStorage.getItem('kajuu_api_key');
    if (key) {
      settings.apiKey = key;
      apiKeyInput.value = key;
      apiKeyInput.type = 'password';
    }
    styleSelect.value = settings.style;
    fontSlider.value = settings.fontSize;
    fontSizeVal.textContent = settings.fontSize;
    document.body.style.fontSize = settings.fontSize + 'px';
  } catch (e) {}
}

function saveSettings() {
  try {
    localStorage.setItem('kajuu_settings', JSON.stringify(settings));
  } catch (e) {}
}

settingsBtn.addEventListener('click', () => settingsPanel.classList.toggle('open'));
settingsClose.addEventListener('click', () => settingsPanel.classList.remove('open'));
overlay.addEventListener('click', () => {
  settingsPanel.classList.remove('open');
  if (window.innerWidth <= 768 && document.querySelector('.sidebar.open')) {
    document.getElementById('sidebarToggle').click();
  }
});

apiKeyInput.addEventListener('change', () => {
  const val = apiKeyInput.value.trim();
  if (val) {
    settings.apiKey = val;
    localStorage.setItem('kajuu_api_key', val);
    showAlert('API key saved');
    saveSettings();
  }
});

toggleApi.addEventListener('click', () => {
  const isPw = apiKeyInput.type === 'password';
  apiKeyInput.type = isPw ? 'text' : 'password';
  toggleApi.innerHTML = isPw
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.83 3.2"/><path d="M9.9 14.44a3 3 0 0 0 4.2 4.2"/><path d="M14.12 9.88a3 3 0 0 0-4.24 4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
});

styleSelect.addEventListener('change', () => {
  settings.style = styleSelect.value;
  saveSettings();
});

fontSlider.addEventListener('input', () => {
  const val = fontSlider.value;
  fontSizeVal.textContent = val;
  settings.fontSize = parseInt(val);
  document.body.style.fontSize = val + 'px';
  saveSettings();
});

clearDataBtn.addEventListener('click', () => {
  if (!confirm('Delete ALL data? This cannot be undone.')) return;
  localStorage.clear();
  if (navigator.serviceWorker) {
    caches.keys().then(names => names.forEach(n => caches.delete(n)));
  }
  location.reload();
});

window.KAJUU_SETTINGS = settings;

// Expose showAlert globally for other modules
window.showAlert = showAlert;
window.loadSettings = loadSettings;
window.saveSettings = saveSettings;

loadSettings();

})();

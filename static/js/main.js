(function() {
'use strict';

function init() {
  // Load history from server, fallback to localStorage
  const p = window.loadHistoryFromServer ? window.loadHistoryFromServer() : Promise.resolve();

  p.then(() => {
    // If no chat selected, select first or show welcome
    const state = window.KAJUU_STATE;
    if (state.currentChatId) {
      const chat = state.chats.find(c => c.id === state.currentChatId);
      if (chat) {
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('messagesContainer').classList.remove('hidden');
        window.renderMessages(chat.messages);
        document.getElementById('chatTitleInput').value = chat.title;
      }
    }

    // Check API key status from server first
    fetch('/api/settings/apikey?user_id=default')
      .then(r => r.json())
      .then(data => {
        if (data.configured) {
          if (!window.KAJUU_SETTINGS.apiKey) {
            window.KAJUU_SETTINGS.apiKey = 'global_configured_key';
            const apiKeyInput = document.getElementById('apiKeyInput');
            if (apiKeyInput) apiKeyInput.placeholder = 'Configured globally on server (Ready)';
          }
        } else {
          // If not configured globally and not configured locally
          if (!window.KAJUU_SETTINGS.apiKey) {
            setTimeout(() => {
              window.showAlert('Enter API key in Settings', false);
              document.getElementById('settingsPanel').classList.add('open');
            }, 800);
          }
        }
      }).catch(() => {
        // Fallback
        if (!window.KAJUU_SETTINGS.apiKey) {
          setTimeout(() => {
            window.showAlert('Enter API key in Settings', false);
            document.getElementById('settingsPanel').classList.add('open');
          }, 800);
        }
      });
  });

  // Auto-save every 30 seconds
  setInterval(() => {
    if (window.syncHistoryToServer) window.syncHistoryToServer();
    // Also save to localStorage
    try {
      if (window.KAJUU_STATE.chats) {
        localStorage.setItem('kajuu_chats', JSON.stringify(window.KAJUU_STATE.chats.slice(0, 20)));
      }
    } catch (e) {}
  }, 30000);
}

// Run on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

})();

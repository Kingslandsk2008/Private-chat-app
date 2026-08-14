(function() {
'use strict';

const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const chatHistory = document.getElementById('chatHistory');
const newChatBtn = document.getElementById('newChatBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesContainer = document.getElementById('messagesContainer');
const chatTitle = document.getElementById('chatTitleInput');
const overlay = document.getElementById('overlay');

const state = window.KAJUU_STATE;
if (!state) {
  window.KAJUU_STATE = {
    chats: [],
    currentChatId: null,
    sidebarOpen: window.innerWidth > 768,
    isMobile: window.innerWidth <= 768,
  };
}
const _state = window.KAJUU_STATE;

function formatTime(ts) {
  const d = new Date(ts);
  const now = new Date();
  const same = d.toDateString() === now.toDateString();
  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (same) return time;
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' + time;
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function getCurrentChat() {
  return _state.chats.find(c => c.id === _state.currentChatId);
}

function selectChat(id) {
  const chat = _state.chats.find(c => c.id === id);
  if (!chat) return;
  _state.currentChatId = id;
  chatTitle.value = chat.title;
  renderSidebar();
  welcomeScreen.classList.add('hidden');
  messagesContainer.classList.remove('hidden');
  if (window.renderMessages) {
    window.renderMessages(chat.messages);
  }
  if (_state.isMobile && _state.sidebarOpen) toggleSidebar();
}

function toggleSidebar() {
  _state.sidebarOpen = !_state.sidebarOpen;
  if (_state.isMobile) {
    sidebar.classList.toggle('open', _state.sidebarOpen);
    overlay.classList.toggle('show', _state.sidebarOpen);
    if (_state.sidebarOpen) overlay.onclick = toggleSidebar;
  } else {
    sidebar.classList.toggle('closed', !_state.sidebarOpen);
    overlay.classList.remove('show');
  }
}

function renderSidebar() {
  chatHistory.innerHTML = _state.chats.slice(0, 10).map(c => `
    <div class="chat-history-item${c.id === _state.currentChatId ? ' active' : ''}" data-id="${c.id}">
      <span class="c-title">${escapeHtml(c.title)}</span>
      <span class="c-time">${formatTime(c.createdAt)}</span>
    </div>
  `).join('');

  chatHistory.querySelectorAll('.chat-history-item').forEach(el => {
    el.addEventListener('click', () => selectChat(el.dataset.id));
    el.addEventListener('dblclick', () => {
      if (confirm('Delete this chat?')) {
        const id = el.dataset.id;
        const idx = _state.chats.findIndex(c => c.id === id);
        if (idx > -1) _state.chats.splice(idx, 1);
        if (_state.currentChatId === id) {
          _state.currentChatId = null;
          welcomeScreen.classList.remove('hidden');
          messagesContainer.classList.add('hidden');
          chatTitle.value = 'New Chat';
        }
        renderSidebar();
      }
    });
  });
}

function newChat() {
  const chat = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
    title: 'New Chat',
    messages: [],
    createdAt: Date.now(),
  };
  _state.chats.unshift(chat);
  _state.currentChatId = chat.id;
  renderSidebar();
  welcomeScreen.classList.add('hidden');
  messagesContainer.classList.remove('hidden');
  messagesContainer.innerHTML = '';
  chatTitle.value = 'New Chat';
  document.getElementById('chatContainer').scrollTop = 0;
}

function newChatFromWelcome() {
  newChat();
  const input = document.getElementById('chatInput');
  input.focus();
}

function clearHistory() {
  if (!_state.chats.length) return;
  if (!confirm('Clear all chat history? This cannot be undone.')) return;
  _state.chats = [];
  _state.currentChatId = null;
  welcomeScreen.classList.remove('hidden');
  messagesContainer.classList.add('hidden');
  chatTitle.value = 'New Chat';
  renderSidebar();
}

// Network sync
function syncHistoryToServer() {
  try {
    const body = JSON.stringify({ user_id: 'default', chats: _state.chats.slice(0, 20) });
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/history', body);
    } else {
      fetch('/api/history', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
    }
  } catch (e) {}
}

async function loadHistoryFromServer() {
  try {
    const resp = await fetch('/api/history?user_id=default');
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.length) {
        _state.chats = data;
        renderSidebar();
        if (!_state.currentChatId) {
          selectChat(data[0].id);
        }
      }
    }
  } catch (e) {
    // Fallback to localStorage
    try {
      const local = localStorage.getItem('kajuu_chats');
      if (local) {
        _state.chats = JSON.parse(local);
        renderSidebar();
      }
    } catch (e2) {}
  }
}

// Event listeners
sidebarToggle.addEventListener('click', toggleSidebar);
newChatBtn.addEventListener('click', newChat);
clearHistoryBtn.addEventListener('click', clearHistory);

// Also wire the welcome screen K logo (double-click to start chat)
document.querySelector('.welcome-logo')?.addEventListener('dblclick', newChatFromWelcome);

// Chat title editing
chatTitle.addEventListener('focus', function() { this.readOnly = false; });
chatTitle.addEventListener('blur', function() {
  this.readOnly = true;
  const chat = getCurrentChat();
  if (chat) {
    chat.title = this.value || 'New Chat';
    renderSidebar();
  }
});
chatTitle.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') this.blur();
});

window.addEventListener('resize', () => {
  const isM = window.innerWidth <= 768;
  if (_state.isMobile !== isM) {
    _state.isMobile = isM;
    if (isM) {
      sidebar.classList.remove('closed');
      sidebar.classList.add('open');
      _state.sidebarOpen = true;
    } else {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    }
  }
});

// Exports
window.KAJUU_STATE = _state;
window.syncHistoryToServer = syncHistoryToServer;
window.loadHistoryFromServer = loadHistoryFromServer;
window.renderSidebar = renderSidebar;
window.newChat = newChat;
window.selectChat = selectChat;
window.getCurrentChat = getCurrentChat;
window.escapeHtml = escapeHtml;
window.formatTime = formatTime;

})();

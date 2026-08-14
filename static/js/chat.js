(function() {
'use strict';

const state = window.KAJUU_STATE;
const settings = window.KAJUU_SETTINGS;
const chatContainer = document.getElementById('chatContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesContainer = document.getElementById('messagesContainer');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const exportBtn = document.getElementById('exportBtn');

let isGenerating = false;

function renderMessages(messages) {
  messagesContainer.innerHTML = '';
  if (!messages || !messages.length) {
    welcomeScreen.classList.remove('hidden');
    messagesContainer.classList.add('hidden');
    return;
  }
  welcomeScreen.classList.add('hidden');
  messagesContainer.classList.remove('hidden');
  messages.forEach(m => appendMessageElement(m.role, m.text, m.timestamp));
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendMessageElement(role, text, timestamp) {
  const div = document.createElement('div');
  div.className = 'message ' + role;
  const isUser = role === 'user';
  const time = timestamp
    ? window.formatTime(timestamp)
    : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const authorHTML = isUser
    ? '<div class="msg-author">You <span class="user-avatar" style="width:20px;height:20px;font-size:10px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--gradient-primary);color:#fff;font-weight:600;">GU</span></div>'
    : '<div class="msg-author"><span class="avatar-small">K</span> KAJUU</div>';
  const processed = isUser ? window.escapeHtml(text) : renderMarkdown(text);
  div.innerHTML = '<div class="bubble">' + processed + '</div><div class="msg-meta">' + authorHTML + ' <span>' + time + '</span></div>';
  messagesContainer.appendChild(div);
  attachCodeCopyHandlers(div);
}

function renderMarkdown(text) {
  if (!text) return '';
  let html;
  try {
    html = marked.parse(text, { breaks: true, gfm: true });
  } catch (e) {
    html = '<p>' + window.escapeHtml(text) + '</p>';
  }
  html = html.replace(/<code(?!\s)/g, '<code class="inline-code"');
  html = html.replace(/<code\s/g, '<code class="inline-code" ');
  const container = document.createElement('div');
  container.innerHTML = html;
  container.querySelectorAll('pre code').forEach(block => {
    try { hljs.highlightBlock(block); } catch (e) {}
  });
  return container.innerHTML;
}

function attachCodeCopyHandlers(container) {
  container.querySelectorAll('pre code').forEach(codeBlock => {
    const pre = codeBlock.parentElement;
    const header = document.createElement('div');
    header.className = 'code-header';
    const lang = (codeBlock.className.match(/language-(\w+)/) || ['', 'code'])[1];
    header.innerHTML = '<span>' + lang + '</span><button class="copy-btn">Copy</button>';
    pre.insertBefore(header, codeBlock);
    header.querySelector('.copy-btn').addEventListener('click', async function() {
      try {
        await navigator.clipboard.writeText(codeBlock.textContent);
        this.textContent = 'Copied!';
        setTimeout(() => { this.textContent = 'Copy'; }, 1500);
      } catch (e) {}
    });
  });
}

function showTyping() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = 'typingIndicator';
  div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  messagesContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function getCurrentChat() {
  if (!state || !state.currentChatId) return null;
  return state.chats.find(c => c.id === state.currentChatId);
}

function getOrCreateChat() {
  let chat = getCurrentChat();
  if (!chat) {
    chat = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
    };
    state.chats.unshift(chat);
    state.currentChatId = chat.id;
  }
  return chat;
}

async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || isGenerating) return;
  if (!settings.apiKey) {
    window.showAlert('Enter API key in Settings', true);
    return;
  }

  const chat = getOrCreateChat();
  chat.messages.push({ role: 'user', text, timestamp: Date.now() });

  // Auto-title
  const userMsgs = chat.messages.filter(m => m.role === 'user');
  if (userMsgs.length === 1) {
    chat.title = text.slice(0, 40) + (text.length > 40 ? '...' : '');
    document.getElementById('chatTitleInput').value = chat.title;
  }

  renderMessages(chat.messages);
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;
  isGenerating = true;

  // Build payload
  const msgs = chat.messages.slice(-20).map(m => ({ role: m.role, content: m.text }));

  showTyping();

  try {
    const modelKey = getSelectedModel();

    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'default',
        messages: msgs,
        model: modelKey,
        style: settings.style,
      }),
    });

    hideTyping();

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || 'HTTP ' + resp.status);
    }

    const data = await resp.json();
    const reply = data.reply || '';

    chat.messages.push({ role: 'assistant', text: reply, timestamp: Date.now() });
    renderMessages(chat.messages);
    window.renderSidebar();

  } catch (error) {
    hideTyping();
    window.showAlert('Error: ' + error.message, true);
    chat.messages.push({
      role: 'assistant',
      text: 'Sorry, I encountered an error: ' + error.message + '\n\nPlease check your connection and API key, then try again.',
      timestamp: Date.now(),
    });
    renderMessages(chat.messages);
    window.renderSidebar();
  } finally {
    isGenerating = false;
    sendBtn.disabled = !chatInput.value.trim();
  }
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
  sendBtn.disabled = !chatInput.value.trim() || isGenerating;
});

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Suggestion cards
document.querySelectorAll('.suggestion-card').forEach(card => {
  card.addEventListener('click', () => {
    const prompt = card.dataset.prompt;
    if (prompt) {
      chatInput.value = prompt;
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
      sendBtn.disabled = false;
    }
  });
});

// Model selector - dynamic from OpenRouter
async function loadModels() {
  try {
    const resp = await fetch('/api/models');
    const data = await resp.json();
    const container = document.getElementById('modelSelectorInner');
    if (!container) return;

    // Keep Free Router first, then add real models
    container.innerHTML = '';

    const defaultBtn = document.createElement('button');
    defaultBtn.className = 'model-btn active';
    defaultBtn.dataset.model = 'openrouter/free';
    defaultBtn.title = 'OpenRouter free model router';
    defaultBtn.innerHTML = '<span class="model-name">Free Router</span><span class="model-provider">OpenRouter</span>';
    container.appendChild(defaultBtn);

    data.models.forEach(m => {
      if (m.id === 'openrouter/free') return;
      const btn = document.createElement('button');
      btn.className = 'model-btn';
      btn.dataset.model = m.id;
      btn.title = `${m.name} | ${m.context.toLocaleString()} context`;
      const shortId = m.id.length > 28 ? m.id.slice(0, 25) + '...' : m.id;
      btn.innerHTML = `<span class="model-name">${shortId}</span><span class="model-provider">${m.provider || 'openrouter'}</span>`;
      container.appendChild(btn);
    });

    // Re-bind click handlers
    container.querySelectorAll('.model-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        // Save selected model
        localStorage.setItem('kajuu_selected_model', btn.dataset.model);
      });
    });

    // Restore previously selected model
    const saved = localStorage.getItem('kajuu_selected_model');
    if (saved) {
      const savedBtn = container.querySelector(`[data-model="${saved}"]`);
      if (savedBtn) {
        container.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
        savedBtn.classList.add('active');
      }
    }
    return data;
  } catch (e) {
    console.warn('Failed to load models:', e);
  }
}

// Apply selected model in chat send
function getSelectedModel() {
  const activeBtn = document.querySelector('.model-btn.active');
  return activeBtn ? activeBtn.dataset.model : 'openrouter/free';
}

// Load models on init
loadModels();

// Refresh models button
document.getElementById('refreshModelsBtn')?.addEventListener('click', async () => {
  document.getElementById('refreshModelsBtn').classList.add('spinning');
  try {
    await fetch('/api/models/refresh', { method: 'POST' });
    await loadModels();
  } catch (e) {}
  document.getElementById('refreshModelsBtn').classList.remove('spinning');
});

// Export
exportBtn.addEventListener('click', () => {
  const chat = getCurrentChat();
  if (!chat || !chat.messages.length) {
    window.showAlert('No messages to export');
    return;
  }
  const text = chat.messages.map(m => {
    const role = m.role === 'user' ? 'You' : 'KAJUU';
    const ts = m.timestamp ? new Date(m.timestamp).toISOString() : new Date().toISOString();
    return '[' + ts + '] ' + role + ':\n' + m.text + '\n\n';
  }).join('---\n\n');
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (chat.title || 'kajuu-chat').replace(/[^a-z0-9 ]/gi, '_') + '.txt';
  a.click();
  URL.revokeObjectURL(url);
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
    e.preventDefault();
    document.getElementById('sidebarToggle').click();
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
    e.preventDefault();
    window.newChat();
  }
  if (e.key === 'Escape') {
    document.getElementById('settingsPanel').classList.remove('open');
  }
});

// Exports
window.renderMessages = renderMessages;
window.appendMessageElement = appendMessageElement;

})();

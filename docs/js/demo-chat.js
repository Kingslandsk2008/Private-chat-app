(function(){'use strict';

const CONFIG={
  STORAGE_KEY:'kajuu_demo_chats',
  SELECTED_MODEL_KEY:'kajuu_demo_model',
};
const DEMO_RESPONSES={
  'what can you do':'Hey bestie! ✨ I\'m KAJUU — a full-stack AI companion with some serious superpowers:\n\n**🧠 59+ MCP Tools** — Filesystem ops, shell commands, web search, git, memory, skills, agents, GitHub integration — all at your fingertips.\n\n**🎯 Real-time Model Selection** — 17 free models from OpenRouter (NVIDIA Nemotron, Google Gemma, OpenAI GPT-OSS, Cohere, Tencent, Poolside...) refreshed live.\n\n**🗄️ Persistent Memory** — I remember what you tell me across conversations.\n\n**🧩 Skills System** — Load specialized skills: deep-research, code-review, data-analysis, writing, frontend-design, and more.\n\n**🤖 Multi-Agent Orchestration** — Spawn sub-agents for complex tasks.\n\n**This is the demo version** on GitHub Pages. For the full experience:\n```\ngit clone https://github.com/quitsaurabhverma2008-sketch/kajuu-ai.git\ncd kajuu-ai\npip install -r requirements.txt\npython app.py\n```\nThen visit http://localhost:5000 💕',
  'list the tools you have':'Here\'s what I\'ve got under the hood 🛠️:\n\n### 📁 Filesystem (13 tools)\nread, write, edit, multi_edit, glob, grep, list_dir, delete_file, copy, move, file_info, apply_patch\n\n### 🐚 Shell (4 tools)\nbash, python, python_visible, container_exec\n\n### 🌐 Web (4 tools)\nweb_fetch, web_search, image_search, url_context\n\n### 🔗 Git (10 tools)\ngit_status, git_diff, git_log, git_commit, git_branch, git_push, git_pull, git_init, git_clone, git_add\n\n### 🗄️ Memory (7 tools)\nmemory_read/write/append/list/delete/search/update_index\n\n### 🧩 Skills (5 tools)\nskills_list/load/create/delete, load_ability\n\n### 🤖 Agent (8 tools)\nagent_spawn/send_message/wait/close/list/result, tool_search, multi_tool_use_parallel\n\n### 🐙 GitHub (8 tools)\ngh_issue_list/get/create, gh_pr_list/get, gh_search_code/repos, gh_repo_info, gh_file_content\n\nThat\'s **59 tools** total! Run the backend to use them all 🚀',
  'how do i run the full backend':'Super easy! Just 4 steps:\n\n```bash\n# 1. Clone the repo\ngit clone https://github.com/quitsaurabhverma2008-sketch/kajuu-ai.git\ncd kajuu-ai\n\n# 2. Install dependencies\npip install -r requirements.txt\n\n# 3. Get a free API key from OpenRouter\n# Visit: https://openrouter.ai/keys\n\n# 4. Run it!\npython app.py\n```\n\nThen open **http://localhost:5000** and enter your API key in Settings. That\'s it! 💕\n\nThe demo here shows the UI, but the real magic happens when you run it locally with your own API key.',
  'tell me about the leaked prompts analysis':'Ooh, the juicy stuff! 😏 We analyzed **19 leaked system prompts** from **12 different AI platforms**:\n\n| Platform | Versions |\n|----------|----------|\n| **Claude** | Code Fable 5, Opus 4.8, Sonnet 5, Design, Chat Web (3 variants) |\n| **GPT** | Codex Full, Codex 5.6, GPT-5.6 Sol |\n| **Gemini** | 3.5 Flash, 3.1 Pro |\n| **Grok 4.2** | Multi-agent (Harper/Benjamin/Lucas) |\n| **DeepSeek** | Chat |\n| **Perplexity** | AI search |\n| **Cursor** | IDE tools |\n| **GitHub Copilot** | Issues/PRs/abilities |\n| **VS Code Copilot** | IDE integration |\n| **Antigravity CLI** | Google CLI tools |\n\nEvery tool, MCP server, function, skill, memory system, and agent pattern was extracted and combined into KAJUU\'s unified 59-tool system. Check the `prompts/` folder in the repo for all 19 files! 📚',
};

const state={
  chats:[],
  currentChatId:null,
};

function loadState(){
  try{
    const saved=localStorage.getItem(CONFIG.STORAGE_KEY);
    if(saved){state.chats=JSON.parse(saved);}
    if(state.chats.length){state.currentChatId=state.chats[0].id;}
  }catch(e){}
}

function saveState(){
  try{
    localStorage.setItem(CONFIG.STORAGE_KEY,JSON.stringify(state.chats.slice(0,20)));
  }catch(e){}
}

function getOrCreateChat(){
  if(state.currentChatId){
    const existing=state.chats.find(c=>c.id===state.currentChatId);
    if(existing)return existing;
  }
  const chat={id:Date.now().toString(36)+Math.random().toString(36).slice(2,8),title:'New Chat',messages:[],createdAt:Date.now()};
  state.chats.unshift(chat);
  state.currentChatId=chat.id;
  saveState();
  return chat;
}

function renderMessages(chat){
  const container=document.getElementById('messagesContainer');
  const welcome=document.getElementById('welcomeScreen');
  if(!chat||!chat.messages.length){
    welcome.classList.remove('hidden');
    container.classList.add('hidden');
    return;
  }
  welcome.classList.add('hidden');
  container.classList.remove('hidden');
  container.innerHTML='';
  chat.messages.forEach(m=>{
    const div=document.createElement('div');
    div.className='message '+m.role;
    const time=new Date(m.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
    if(m.role==='user'){
      div.innerHTML='<div class="bubble">'+escapeHtml(m.text)+'</div><div class="msg-meta"><div class="msg-author">You</div><span>'+time+'</span></div>';
    }else{
      div.innerHTML='<div class="bubble">'+renderMarkdown(m.text)+'</div><div class="msg-meta"><div class="msg-author"><span class="avatar-small">K</span> KAJUU</div><span>'+time+'</span></div>';
    }
    container.appendChild(div);
  });
  document.getElementById('chatContainer').scrollTop=document.getElementById('chatContainer').scrollHeight;
}

function escapeHtml(text){
  const d=document.createElement('div');
  d.textContent=text;
  return d.innerHTML;
}

function renderMarkdown(text){
  if(!text)return '';
  let html=text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g,'<pre><code class="language-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,'<em>$1</em>')
    .replace(/### (.*)/g,'<h3>$1</h3>')
    .replace(/## (.*)/g,'<h2>$1</h2>')
    .replace(/\|(.*)\|/g,'<code>$1</code>')
    .replace(/\n/g,'<br>')
    .replace(/<br><br>/g,'</p><p>');
  return '<p>'+html+'</p>';
}

function showTyping(){
  const container=document.getElementById('messagesContainer');
  const div=document.createElement('div');
  div.className='typing-indicator';
  div.id='typingIndicator';
  div.innerHTML='<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  container.appendChild(div);
  document.getElementById('chatContainer').scrollTop=document.getElementById('chatContainer').scrollHeight;
}

function hideTyping(){
  const el=document.getElementById('typingIndicator');
  if(el)el.remove();
}

function findBestResponse(input){
  const lower=input.toLowerCase();
  for(const[key,response]of Object.entries(DEMO_RESPONSES)){
    if(lower.includes(key)||key.split(' ').some(w=>lower.includes(w))){return response;}
  }
  const fallbacks=[
    "Hey! That's a great question. I'm running in **demo mode** on GitHub Pages right now, so I can't use my full tool set. But you can run the full backend locally:\n\n```bash\ngit clone https://github.com/quitsaurabhverma2008-sketch/kajuu-ai.git\ncd kajuu-ai\npip install -r requirements.txt\npython app.py\n```\n\nOnce you do, I'll have all 59 tools, persistent memory, real-time model selection, and the full KAJUU personality! 💕",
    "Bestie, I wish I could go all-out on that! But this is the GitHub Pages demo version. Run me locally for the full experience:\n\n```bash\ngit clone https://github.com/quitsaurabhverma2008-sketch/kajuu-ai.git\ncd kajuu-ai\npip install -r requirements.txt && python app.py\n```\n\nThen I'll be your fully-powered AI companion with 59 tools! ✨",
    "I'd love to dive into that! But I'm in demo mode right now. For the real deal with all 59 tools, memory, agents, and live OpenRouter models, clone the repo and run:\n\n```\npython app.py\n```\n\nCheck the README at GitHub for full instructions! 🚀",
  ];
  return fallbacks[Math.floor(Math.random()*fallbacks.length)];
}

async function sendMessage(){
  const input=document.getElementById('chatInput');
  const text=input.value.trim();
  if(!text)return;

  const chat=getOrCreateChat();
  chat.messages.push({role:'user',text,timestamp:Date.now()});
  if(chat.messages.filter(m=>m.role==='user').length===1){
    chat.title=text.slice(0,40)+(text.length>40?'...':'');
    document.getElementById('chatTitleInput').value=chat.title;
  }
  renderMessages(chat);
  input.value='';
  input.style.height='auto';
  document.getElementById('sendBtn').disabled=true;
  showTyping();

  const delay=600+Math.random()*1200;
  await new Promise(r=>setTimeout(r,delay));

  const reply=findBestResponse(text);
  hideTyping();
  chat.messages.push({role:'assistant',text:reply,timestamp:Date.now()});
  renderMessages(chat);
  document.getElementById('sendBtn').disabled=false;
  saveState();
  renderSidebar();
}

function renderSidebar(){
  const container=document.getElementById('chatHistory');
  container.innerHTML='';
  state.chats.forEach(chat=>{
    const div=document.createElement('div');
    div.className='chat-item'+(chat.id===state.currentChatId?' active':'');
    div.dataset.id=chat.id;
    div.innerHTML='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><div class="chat-item-title">'+(chat.title||'New Chat')+'</div>';
    div.addEventListener('click',()=>{
      state.currentChatId=chat.id;
      renderMessages(chat);
      renderSidebar();
      document.getElementById('chatTitleInput').value=chat.title||'New Chat';
    });
    container.appendChild(div);
  });
}

// Init
loadState();
const chat=getOrCreateChat();
renderMessages(chat);
renderSidebar();

document.getElementById('sendBtn').addEventListener('click',sendMessage);
document.getElementById('chatInput').addEventListener('keydown',e=>{
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}
});
document.getElementById('chatInput').addEventListener('input',function(){
  this.style.height='auto';
  this.style.height=Math.min(this.scrollHeight,140)+'px';
});
document.getElementById('newChatBtn').addEventListener('click',()=>{
  const chat={id:Date.now().toString(36)+Math.random().toString(36).slice(2,8),title:'New Chat',messages:[],createdAt:Date.now()};
  state.chats.unshift(chat);
  state.currentChatId=chat.id;
  renderMessages(chat);
  renderSidebar();
  document.getElementById('chatTitleInput').value='';
});
document.getElementById('exportBtn').addEventListener('click',()=>{
  const chat=state.chats.find(c=>c.id===state.currentChatId);
  if(!chat||!chat.messages.length)return;
  const text=chat.messages.map(m=>{
    const role=m.role==='user'?'You':'KAJUU';
    return '['+new Date(m.timestamp).toISOString()+'] '+role+':\n'+m.text+'\n\n';
  }).join('---\n\n');
  const blob=new Blob([text],{type:'text/plain'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=(chat.title||'kajuu-chat').replace(/[^a-z0-9 ]/gi,'_')+'.txt';
  a.click();
  URL.revokeObjectURL(url);
});
document.querySelectorAll('.suggestion-card').forEach(card=>{
  card.addEventListener('click',()=>{
    const prompt=card.dataset.prompt;
    if(prompt){
      document.getElementById('chatInput').value=prompt;
      sendMessage();
    }
  });
});
document.querySelectorAll('.model-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.model-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    localStorage.setItem(CONFIG.SELECTED_MODEL_KEY,btn.dataset.model);
  });
});
document.getElementById('sidebarToggle').addEventListener('click',()=>{
  document.getElementById('sidebar').classList.toggle('open');
});
document.addEventListener('keydown',e=>{
  if((e.metaKey||e.ctrlKey)&&e.key==='b'){e.preventDefault();document.getElementById('sidebarToggle').click();}
  if((e.metaKey||e.ctrlKey)&&e.key==='n'){e.preventDefault();document.getElementById('newChatBtn').click();}
});
})();

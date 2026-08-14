# KAJUU.AI 🚀

<div align="center">

![KAJUU.AI](assets/chat-preview.png)

**Full-stack AI chat application with 59+ MCP tools, real-time OpenRouter model selection, persistent memory, skills system, multi-agent orchestration, and git/GitHub integration.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Free%20Models-FF6B6B?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![Three.js](https://img.shields.io/badge/Three.js-r128-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Features

### 🧠 Real-Time Model Selection
![Real-time model fetching from OpenRouter](assets/models-preview.png)

Dynamically fetches **all free models** from OpenRouter's live API every 5 minutes. Currently **17 free models** available including:
- NVIDIA Nemotron 3 Ultra (1M context)
- Google Gemma 4 / Lyria 3 (1M context)
- OpenAI GPT-OSS 20B
- Cohere North Mini Code
- Tencent Hy3
- Poolside Laguna models
- And more — refreshed automatically

### 🛠️ 59+ MCP Tools from Leaked Prompt Analysis
![MCP Tools System](assets/tools-demo.png)

Every tool cataloged from analyzing **19 leaked system prompts** from:
- **Claude** (Code Fable 5, Opus 4.8, Sonnet 5, Design, Chat Web)
- **GPT** (Codex Full, Codex 5.6, GPT-5.6 Sol)
- **Gemini** (3.5 Flash, 3.1 Pro)
- **Grok 4.2** (Multi-agent system with Harper/Benjamin/Lucas)
- **Cursor, Copilot, VS Code Copilot, Perplexity, DeepSeek**

| Tool Module | Count | Capabilities |
|-------------|-------|-------------|
| `filesystem` | 13 | Read, Write, Edit, Multi-Edit, Glob, Grep, List Dir, Delete, Copy, Move, File Info, Apply Patch |
| `shell` | 4 | Bash, Python, Python Visible, Container Exec |
| `web` | 4 | Web Fetch, Web Search, Image Search, URL Context |
| `git` | 10 | Status, Diff, Log, Commit, Branch, Push, Pull, Init, Clone, Add |
| `memory` | 7 | Read, Write, Append, List, Delete, Search, Index |
| `skills` | 5 | List, Load, Create, Delete, Load Ability |
| `agent` | 8 | Spawn, Send Message, Wait, Close, List, Result, Tool Search, Parallel |
| `github` | 8 | Issues (CRUD), PRs (List/Get), Search Code/Repos, Repo Info, File Content |

### 🗄️ Persistent Memory System
Full hierarchical markdown-based memory with search, append, index, and concurrent-write protection — inspired by Claude chat web's memory system.

### 🎨 Glassmorphism UI
Dark theme with Three.js WebGL shader background, backdrop-filter blur effects, and smooth animations.

### 🌐 API Proxy
Routes all requests through OpenRouter — no direct API key exposure on client side.

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/quitsaurabhverma2008-sketch/kajuu-ai.git
cd kajuu-ai

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open `http://localhost:5000` and enter your OpenRouter API key in Settings.

> **Get a free API key:** https://openrouter.ai/keys

---

## 📁 Project Structure

```
kajuu-ai/
├── app.py                      # Flask backend (500+ lines, all endpoints)
├── kajuu_system_prompt.md      # KAJUU's personality system prompt (v5.0)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── assets/                     # README images
├── tools/                      # MCP Tool implementations (59 tools)
│   ├── __init__.py             # ToolRegistry
│   ├── filesystem.py           # File ops (read/write/edit/glob/grep...)
│   ├── shell.py                # Bash/Python/Container exec
│   ├── web.py                  # Web fetch/search
│   ├── git.py                  # Git operations
│   ├── memory.py               # Persistent memory
│   ├── skills.py               # Skills/plugin system
│   ├── agent.py                # Multi-agent orchestration
│   └── github.py               # GitHub API tools
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism design system
│   └── js/
│       ├── three-background.js  # Three.js WebGL background
│       ├── chat.js              # Chat logic & model selector
│       ├── sidebar.js           # History sidebar
│       ├── settings.js          # Settings panel
│       ├── tools.js             # Frontend tool API wrappers
│       └── main.js              # App initialization
├── templates/
│   └── index.html               # Single-page app
├── prompts/                     # 19 leaked system prompt files
│   ├── anthropic_claude_code_fable_5.md
│   ├── openai_codex_full.md
│   ├── google_gemini_3.1_pro.md
│   ├── xai_grok_4.2.md
│   └── ... (19 total)
└── data/                        # Runtime data (auto-created)
    ├── memory/                  # User memory documents
    ├── skills/                  # Skill definitions
    └── uploads/                 # File uploads
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application |
| `/api/chat` | POST | Send message to AI |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/models` | GET | List all free OpenRouter models |
| `/api/models/refresh` | POST | Force-refresh model list |
| `/api/tools` | GET | List all 59 tools |
| `/api/tools/call` | POST | Execute any tool |
| `/api/tools/parallel` | POST | Execute tools in parallel |
| `/api/tools/search` | POST | Search tools by keyword |
| `/api/tools/shell` | POST | Execute shell command |
| `/api/tools/python` | POST | Execute Python code |
| `/api/agent/spawn` | POST | Spawn a sub-agent |
| `/api/agents` | GET | List running agents |
| `/api/agent/<id>/wait` | GET | Wait for agent completion |
| `/api/agent/<id>/result` | GET | Get agent result |
| `/api/memory` | GET/POST | List/write memory documents |
| `/api/memory/<name>` | GET/DELETE | Read/delete memory document |
| `/api/memory/search` | POST | Search memory |
| `/api/skills` | GET/POST | List/create skills |
| `/api/skills/<name>` | GET/DELETE | Load/delete skill |
| `/api/history` | GET/POST | Chat history |
| `/api/settings/apikey` | GET/POST | API key management |
| `/api/upload` | POST | File upload |
| `/api/prompts` | GET | List leaked prompt files |

---

## 🔧 Tool Usage (Frontend)

```javascript
// All tools available via KAJUU_TOOLS object

// Filesystem
await KAJUU_TOOLS.fs.read('path/to/file.txt');
await KAJUU_TOOLS.fs.write('path/to/file.txt', 'content');
await KAJUU_TOOLS.fs.glob('**/*.py');

// Shell
await KAJUU_TOOLS.shell.bash('ls -la');
await KAJUU_TOOLS.shell.python('print("hello")');

// Web
await KAJUU_TOOLS.web.search('latest AI news');
await KAJUU_TOOLS.web.fetch('https://example.com');

// Git
await KAJUU_TOOLS.git.status();
await KAJUU_TOOLS.git.commit('feat: add new feature');

// Memory
await KAJUU_TOOLS.memory.list();
await KAJUU_TOOLS.memory.write('user-notes', 'content');

// Skills
await KAJUU_TOOLS.skills.list();
await KAJUU_TOOLS.skills.load('deep-research');

// GitHub (requires `gh` CLI)
await KAJUU_TOOLS.github.repoInfo('user/repo');
await KAJUU_TOOLS.github.issueList('user/repo');

// Agent
const agent = await KAJUU_TOOLS.agent.spawn('analyze logs', 'explorer');
```

---

## 🧩 Leaked Prompts Analyzed

19 system prompt files from 12 AI platforms were analyzed to build KAJUU's tool system:

| Platform | Version | Key Contribution |
|----------|---------|-----------------|
| Claude Code | Fable 5, Opus 4.8, Sonnet 5 | Bash, Glob, Grep, Read, Write, Edit, WebFetch, agents |
| Claude Chat | Fable 5, Opus 4.8, Sonnet 5 | Memory system, artifact, skills, image gen, places |
| Claude Design | — | File ops, show_html, design system, verification |
| GPT-5 Codex | Full, 5.6 | multi_agent_v1, shell, file tools, GitHub MCP (50+ tools) |
| ChatGPT 5.6 Sol | — | Gmail, Calendar, Contacts, Python exec, automations |
| Gemini 3.5 Flash | — | Google Search, code_exec, saved_info |
| Gemini 3.1 Pro | — | Image/video/music gen, canvas, scholar search |
| Grok 4.2 | — | Multi-agent (Harper/Benjamin/Lucas), Twitter/X API |
| DeepSeek Chat | — | Search tool |
| Perplexity AI | — | Search with citations, related questions |
| Cursor IDE | — | Shell, Read, Write, Edit, mcp_* |
| GitHub Copilot | — | Issues, PRs, search, abilities (code-review, pr-reviewer) |
| VS Code Copilot | — | Shell, Read, Write, Edit, mcp_* |

---

## 🤝 Contributing

PRs welcome! Ideas:
- Add more MCP servers (filesystem, browser, database)
- Implement streaming tool execution
- Add voice I/O
- Dockerize for easy deployment

---

<div align="center">
Made with ❤️ by <a href="https://github.com/quitsaurabhverma2008-sketch">quitsaurabhverma2008-sketch</a>
</div>

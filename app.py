#!/data/data/com.termux/files/usr/bin/python
"""KAJUU.AI — Flask backend with OpenRouter API proxy, chat history, file handling."""

import os
import json
import uuid
import time
import threading
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.resolve()

def get_writable_data_dir():
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        d = Path("/tmp/kajuu_data")
        d.mkdir(parents=True, exist_ok=True)
        return d
    try:
        d = BASE_DIR / "data"
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / ".write_test"
        test_file.touch()
        test_file.unlink()
        return d
    except Exception:
        d = Path("/tmp/kajuu_data")
        d.mkdir(parents=True, exist_ok=True)
        return d

DATA_DIR = get_writable_data_dir()

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates"),
)
from flask import has_request_context
CORS(app)

PROMPTS_DIR = BASE_DIR / "prompts"
SYSTEM_PROMPT_FILE = BASE_DIR / "kajuu_system_prompt.md"

HISTORY_FILE = DATA_DIR / "chat_history.json"
API_KEYS_FILE = DATA_DIR / "api_keys.json"

# OpenRouter configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_API_URL = "https://openrouter.ai/api/v1/models"
MAX_HISTORY_LENGTH = 100

# Rate limits
MAX_CHAT_TABS = 10
CHAT_EXPIRY_HOURS = 5
MESSAGE_PRUNE_LIMIT = 100

DEFAULT_FREE_MODELS = [
    {"id": "openrouter/free", "name": "Free Router", "provider": "OpenRouter", "context": 128000},
    {"id": "google/gemini-2.0-flash-lite-001:free", "name": "Gemini 2.0 Flash Lite", "provider": "Google", "context": 1048576},
    {"id": "google/gemini-2.0-pro-exp-02-05:free", "name": "Gemini 2.0 Pro Exp", "provider": "Google", "context": 2000000},
    {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1", "provider": "DeepSeek", "context": 16384},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B", "provider": "Meta", "context": 131072},
    {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "name": "Qwen 2.5 Coder 32B", "provider": "Qwen", "context": 32768},
    {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B", "provider": "Mistral", "context": 32768}
]

# Initialize tool registry
from tools import ToolRegistry
TOOL_REGISTRY = ToolRegistry(BASE_DIR, DATA_DIR)


def load_json(path, default=None):
    if not path.exists():
        return default or {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default or {}


def save_json(path, data):
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving JSON to {path}: {e}")


def load_system_prompt():
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE) as f:
            return f.read()
    return "You are KAJUU, a brilliant, friendly AI assistant."


def get_user_api_key(user_id="default"):
    # Check Authorization header first
    if has_request_context():
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer ") and len(auth_hdr) > 10:
            return auth_hdr[7:].strip()
    # env var takes precedence
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key
    keys = load_json(API_KEYS_FILE)
    return keys.get(user_id, "")


def save_user_api_key(user_id, api_key):
    keys = load_json(API_KEYS_FILE)
    keys[user_id] = api_key
    save_json(API_KEYS_FILE, keys)


def get_style_prompt(style):
    prompts = {
        "creative": "You are highly creative and love vivid language, unexpected analogies, and expressive descriptions. Feel free to be poetic.",
        "balanced": "Balance creativity with precision. Be clear and engaging, but keep your feet on the ground.",
        "precise": "Be concise, accurate, and to-the-point. Prefer facts over flair and brevity over elaboration.",
    }
    return prompts.get(style, prompts["balanced"])


# ======================== TAB MANAGEMENT ========================


def get_user_filepath(user_id, filename):
    d = DATA_DIR / "users" / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / filename


def get_user_tabs(user_id):
    return load_json(get_user_filepath(user_id, "tabs.json"), {})


def save_user_tabs(user_id, tabs):
    save_json(get_user_filepath(user_id, "tabs.json"), tabs)


def prune_expired_chats(user_id):
    tabs = get_user_tabs(user_id)
    now = time.time()
    expiry = CHAT_EXPIRY_HOURS * 3600
    changed = False
    for tab_id in list(tabs.keys()):
        if now - tabs[tab_id].get("created_at", 0) > expiry:
            del tabs[tab_id]
            changed = True
    if changed:
        save_user_tabs(user_id, tabs)
    return tabs


def enforce_tab_limit(user_id):
    return len(get_user_tabs(user_id)) < MAX_CHAT_TABS


def get_or_create_tab(user_id, tab_id=None):
    now = time.time()
    tabs = get_user_tabs(user_id)
    if tab_id and tab_id in tabs:
        tabs[tab_id]["last_active"] = now
        save_user_tabs(user_id, tabs)
        return tabs[tab_id]
    if len(tabs) >= MAX_CHAT_TABS:
        oldest = min(tabs.keys(), key=lambda k: tabs[k].get("last_active", 0))
        del tabs[oldest]
    new_tab = {
        "id": tab_id or uuid.uuid4().hex[:12],
        "title": "New Chat",
        "created_at": now,
        "last_active": now,
        "message_count": 0,
    }
    tabs[new_tab["id"]] = new_tab
    save_user_tabs(user_id, tabs)
    return new_tab


def get_tab_chat_history(user_id, tab_id):
    return load_json(get_user_filepath(user_id, f"chat_{tab_id}.json"), [])


def save_tab_chat_history(user_id, tab_id, messages):
    save_json(get_user_filepath(user_id, f"chat_{tab_id}.json"), messages)


def append_tab_message(user_id, tab_id, role, text):
    if not text:
        return
    messages = get_tab_chat_history(user_id, tab_id)
    messages.append({
        "role": role,
        "content": text,
        "timestamp": datetime.utcnow().isoformat(),
    })
    if len(messages) > MESSAGE_PRUNE_LIMIT:
        messages = messages[-MESSAGE_PRUNE_LIMIT:]
    save_tab_chat_history(user_id, tab_id, messages)
    tabs = get_user_tabs(user_id)
    if tab_id in tabs:
        tabs[tab_id]["message_count"] = len(messages)
        tabs[tab_id]["last_active"] = time.time()
        try:
            tabs[tab_id]["title"] = messages[0].get("content", "")[:40] or "New Chat"
        except IndexError:
            tabs[tab_id]["title"] = "New Chat"
        save_user_tabs(user_id, tabs)


def periodic_cleanup():
    while True:
        try:
            users_dir = DATA_DIR / "users"
            if users_dir.exists():
                for entry in users_dir.iterdir():
                    if entry.is_dir():
                        prune_expired_chats(entry.name)
                        now = time.time()
                        expiry = CHAT_EXPIRY_HOURS * 3600
                        for f in entry.glob("chat_*.json"):
                            if now - f.stat().st_mtime > expiry:
                                f.unlink()
        except Exception:
            pass
        time.sleep(300)


if not os.environ.get("VERCEL"):
    threading.Thread(target=periodic_cleanup, daemon=True).start()


# ======================== MODEL FETCHING ========================

MODELS_CACHE_TTL = 300
MODELS_CACHE_FILE = DATA_DIR / "models_cache.json"


def _is_zero_cost(val):
    if val is None:
        return True
    try:
        return float(val) == 0.0
    except (ValueError, TypeError):
        return str(val).strip() in ("0", "0.0", "0.000000")


def fetch_free_models(force_refresh=False):
    now = time.time()
    cache = load_json(MODELS_CACHE_FILE)
    if not force_refresh and cache.get("timestamp") and (now - cache["timestamp"]) < MODELS_CACHE_TTL and cache.get("models"):
        return cache.get("models")
    try:
        resp = requests.get(MODELS_API_URL, timeout=10)
        if resp.ok:
            all_models = resp.json().get("data", [])
            free_models = []
            for m in all_models:
                pricing = m.get("pricing", {})
                prompt_cost = pricing.get("prompt")
                comp_cost = pricing.get("completion")
                if _is_zero_cost(prompt_cost) and _is_zero_cost(comp_cost):
                    free_models.append({
                        "id": m["id"],
                        "name": m.get("name", m["id"]),
                        "provider": m.get("name", "").split(":")[0].strip() if ":" in m.get("name", "") else m["id"].split("/")[0],
                        "context": m.get("context_length", 0),
                    })
            if free_models:
                save_json(MODELS_CACHE_FILE, {"models": free_models, "timestamp": now})
                return free_models
    except Exception as e:
        print(f"Model fetch error: {e}")
    if cache.get("models"):
        return cache["models"]
    return DEFAULT_FREE_MODELS


# Pre-fetch in background if not on Vercel
if not os.environ.get("VERCEL"):
    threading.Thread(target=fetch_free_models, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "5.0",
        "name": "KAJUU.AI",
    })


@app.route("/api/user/tabs", methods=["GET"])
def get_user_tabs_route():
    user_id = request.args.get("user_id", "default")
    tabs = prune_expired_chats(user_id)
    return jsonify({"tabs": tabs, "tabs_used": len(tabs), "tabs_max": MAX_CHAT_TABS})


@app.route("/api/user/tabs", methods=["POST"])
def create_user_tab():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    tab_id = data.get("tab_id")
    if not enforce_tab_limit(user_id):
        return jsonify({
            "error": f"Tab limit reached. Max {MAX_CHAT_TABS} tabs allowed.",
            "tabs_max": MAX_CHAT_TABS,
        }), 403
    tab = get_or_create_tab(user_id, tab_id)
    return jsonify({"tab": tab})


@app.route("/api/user/tabs/<tab_id>", methods=["DELETE"])
def delete_user_tab(tab_id):
    user_id = request.args.get("user_id", "default")
    tabs = get_user_tabs(user_id)
    if tab_id in tabs:
        del tabs[tab_id]
        save_user_tabs(user_id, tabs)
        fpath = get_user_filepath(user_id, f"chat_{tab_id}.json")
        if fpath.exists():
            fpath.unlink()
    return jsonify({"status": "deleted", "tab_id": tab_id})


@app.route("/api/user/tabs/<tab_id>/messages", methods=["GET"])
def get_tab_messages(tab_id):
    user_id = request.args.get("user_id", "default")
    messages = get_tab_chat_history(user_id, tab_id)
    return jsonify({"messages": messages, "count": len(messages)})


@app.route("/api/user/tabs/<tab_id>", methods=["PATCH"])
def rename_tab(tab_id):
    data = request.get_json()
    user_id = data.get("user_id", "default")
    title = data.get("title", "").strip()[:40] or "New Chat"
    tabs = get_user_tabs(user_id)
    if tab_id in tabs:
        tabs[tab_id]["title"] = title
        save_user_tabs(user_id, tabs)
        return jsonify({"status": "renamed", "title": title})
    return jsonify({"error": "Tab not found"}), 404


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(BASE_DIR / "static"), filename)


@app.route("/api/models", methods=["GET"])
def list_models():
    models = fetch_free_models()
    return jsonify({"models": models, "count": len(models), "default": "openrouter/free"})


@app.route("/api/models/refresh", methods=["POST"])
def refresh_models():
    models = fetch_free_models(force_refresh=True)
    return jsonify({"models": models, "count": len(models)})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy to OpenRouter API with per-tab conversation history."""
    data = request.get_json()
    user_id = data.get("user_id", "default")
    tab_id = data.get("tab_id", "default")
    messages = data.get("messages", [])
    model_key = data.get("model", "flash")
    style = data.get("style", "balanced")
    system_override = data.get("system_prompt", "")

    api_key = get_user_api_key(user_id)
    if not api_key:
        return jsonify({"error": "API key not configured. Set it in Settings."}), 401

    valid_models = fetch_free_models()
    valid_ids = {m["id"] for m in valid_models} | {m["id"] for m in DEFAULT_FREE_MODELS}
    model = model_key if (model_key in valid_ids or "/" in model_key or model_key.endswith(":free")) else "openrouter/free"

    base_system = load_system_prompt()
    style_instruction = get_style_prompt(style)
    system_content = f"{base_system}\n\n{style_instruction}"
    if system_override:
        system_content = system_override

    full_messages = [{"role": "system", "content": system_content}]
    full_messages.extend(messages[-MAX_HISTORY_LENGTH:])

    payload = {
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.7 if style == "creative" else (0.3 if style == "precise" else 0.5),
        "messages": full_messages,
    }

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": request.host_url or "https://kajuu.ai",
                "X-Title": "KAJUU.AI",
            },
            json=payload,
            timeout=60,
        )

        if not resp.ok:
            error_body = resp.text
            try:
                err_data = resp.json()
                error_body = err_data.get("error", {}).get("message", error_body)
            except Exception:
                pass
            return jsonify({"error": f"OpenRouter API error: {error_body}"}), resp.status_code

        result = resp.json()
        reply = result["choices"][0]["message"]["content"]

        get_or_create_tab(user_id, tab_id)
        if messages:
            append_tab_message(user_id, tab_id, "user", messages[-1].get("content", ""))
        append_tab_message(user_id, tab_id, "assistant", reply)

        return jsonify({"reply": reply, "model": result.get("model", model)})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connection error. Check your internet."}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming proxy endpoint for Server-Sent Events."""
    data = request.get_json()
    user_id = data.get("user_id", "default")
    tab_id = data.get("tab_id", "default")
    messages = data.get("messages", [])
    model_key = data.get("model", "flash")
    style = data.get("style", "balanced")

    api_key = get_user_api_key(user_id)
    if not api_key:
        return jsonify({"error": "API key not configured"}), 401

    valid_models = fetch_free_models()
    valid_ids = {m["id"] for m in valid_models} | {m["id"] for m in DEFAULT_FREE_MODELS}
    model = model_key if (model_key in valid_ids or "/" in model_key or model_key.endswith(":free")) else "openrouter/free"
    base_system = load_system_prompt()
    style_instruction = get_style_prompt(style)

    full_messages = [{"role": "system", "content": f"{base_system}\n\n{style_instruction}"}]
    full_messages.extend(messages[-MAX_HISTORY_LENGTH:])

    def generate():
        full_text = ""
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": request.host_url or "https://kajuu.ai",
                    "X-Title": "KAJUU.AI",
                },
                json={
                    "model": model,
                    "max_tokens": 2048,
                    "temperature": 0.7 if style == "creative" else (0.3 if style == "precise" else 0.5),
                    "messages": full_messages,
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )

            if not resp.ok:
                yield f"data: {json.dumps({'error': f'HTTP {resp.status_code}'})}\n\n"
                return

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    chunk = decoded[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(chunk)
                        delta = chunk_data["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            full_text += delta
                            yield f"data: {json.dumps({'text': delta})}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue

            yield "data: [DONE]"
            # Save after stream completes
            get_or_create_tab(user_id, tab_id)
            if messages:
                append_tab_message(user_id, tab_id, "user", messages[-1].get("content", ""))
            if full_text:
                append_tab_message(user_id, tab_id, "assistant", full_text)

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            if full_text:
                append_tab_message(user_id, tab_id, "assistant", full_text + f"\n\n[Error: {e}]")

    return app.response_class(generate(), mimetype="text/event-stream")


@app.route("/api/history", methods=["GET"])
def get_history():
    user_id = request.args.get("user_id", "default")
    history = load_json(HISTORY_FILE)
    return jsonify(history.get(user_id, []))


@app.route("/api/history", methods=["POST"])
def save_history():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    chats = data.get("chats", [])

    history = load_json(HISTORY_FILE)
    history[user_id] = chats
    save_json(HISTORY_FILE, history)

    return jsonify({"status": "ok"})


@app.route("/api/history/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    user_id = request.args.get("user_id", "default")
    history = load_json(HISTORY_FILE)
    if user_id in history:
        history[user_id] = [c for c in history[user_id] if c.get("id") != chat_id]
        save_json(HISTORY_FILE, history)
    return jsonify({"status": "ok"})


@app.route("/api/settings/apikey", methods=["POST"])
def set_api_key():
    data = request.get_json()
    user_id = data.get("user_id", "default")
    api_key = data.get("api_key", "")

    if not api_key:
        return jsonify({"error": "API key is required"}), 400

    save_user_api_key(user_id, api_key)
    return jsonify({"status": "ok"})


@app.route("/api/settings/apikey", methods=["GET"])
def get_api_key_status():
    user_id = request.args.get("user_id", "default")
    key = get_user_api_key(user_id)
    return jsonify({"configured": bool(key)})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = upload_dir / filename
    file.save(filepath)

    file_type = file.content_type or "application/octet-stream"
    file_size = filepath.stat().st_size

    # Read content for text files
    content = ""
    if file_type.startswith("text/") or filename.endswith((".py", ".js", ".html", ".css", ".json", ".md", ".txt", ".csv")):
        try:
            content = filepath.read_text("utf-8", errors="replace")
        except Exception:
            content = "[Binary file - content not readable as text]"

    return jsonify({
        "filename": filename,
        "original_name": file.filename,
        "type": file_type,
        "size": file_size,
        "content": content[:100000],  # Limit to 100k chars
    })


@app.route("/api/prompts", methods=["GET"])
def list_prompts():
    """List available system prompt files for reference."""
    prompts = []
    if PROMPTS_DIR.exists():
        for f in sorted(PROMPTS_DIR.glob("*.md")):
            prompts.append({
                "name": f.stem,
                "file": f.name,
                "size": f.stat().st_size,
            })
    return jsonify(prompts)


@app.route("/api/prompts/<filename>", methods=["GET"])
def get_prompt(filename):
    filepath = PROMPTS_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".md":
        return jsonify({"error": "Prompt not found"}), 404
    return jsonify({
        "name": filepath.stem,
        "content": filepath.read_text(),
    })


# ======================== TOOL & MCP ENDPOINTS ========================

@app.route("/api/tools", methods=["GET"])
def list_tools():
    return jsonify(TOOL_REGISTRY.list_tools())


@app.route("/api/tools/call", methods=["POST"])
def call_tool():
    data = request.get_json()
    name = data.get("tool", "")
    params = data.get("params", {})
    result = TOOL_REGISTRY.call_tool(name, **params)
    return jsonify(result)


@app.route("/api/tools/parallel", methods=["POST"])
def call_tools_parallel():
    data = request.get_json()
    calls = data.get("calls", [])
    results = TOOL_REGISTRY.call_tools_parallel(calls)
    return jsonify(results)


@app.route("/api/tools/search", methods=["POST"])
def search_tools():
    data = request.get_json()
    query = data.get("query", "")
    agent = TOOL_REGISTRY.get_tool("tool_search")
    if agent:
        result = agent[0](query=query)
    else:
        result = {"error": "Tool search not available"}
    return jsonify(result)


# ======================== AGENT ENDPOINTS ========================

@app.route("/api/agent/spawn", methods=["POST"])
def agent_spawn():
    data = request.get_json()
    task = data.get("task", "")
    role = data.get("role", "general")
    tool = TOOL_REGISTRY.get_tool("agent_spawn")
    return jsonify(tool[0](task=task, role=role) if tool else {"error": "Agent tool not available"})


@app.route("/api/agent/<agent_id>/wait", methods=["GET"])
def agent_wait(agent_id):
    timeout = request.args.get("timeout", 60, type=int)
    tool = TOOL_REGISTRY.get_tool("agent_wait")
    return jsonify(tool[0](agent_id=agent_id, timeout=timeout) if tool else {"error": "Agent tool not available"})


@app.route("/api/agent/<agent_id>/result", methods=["GET"])
def agent_result(agent_id):
    tool = TOOL_REGISTRY.get_tool("agent_result")
    return jsonify(tool[0](agent_id=agent_id) if tool else {"error": "Agent tool not available"})


@app.route("/api/agent/<agent_id>", methods=["DELETE"])
def agent_close(agent_id):
    tool = TOOL_REGISTRY.get_tool("agent_close")
    return jsonify(tool[0](agent_id=agent_id) if tool else {"error": "Agent tool not available"})


@app.route("/api/agents", methods=["GET"])
def agent_list():
    tool = TOOL_REGISTRY.get_tool("agent_list")
    return jsonify(tool[0]() if tool else {"error": "Agent tool not available"})


# ======================== SKILLS ENDPOINTS ========================

@app.route("/api/skills", methods=["GET"])
def skills_list():
    tool = TOOL_REGISTRY.get_tool("skills_list")
    return jsonify(tool[0]() if tool else {"error": "Skills not available"})


@app.route("/api/skills/<name>", methods=["GET"])
def skills_load(name):
    tool = TOOL_REGISTRY.get_tool("skills_load")
    return jsonify(tool[0](name=name) if tool else {"error": "Skills not available"})


@app.route("/api/skills", methods=["POST"])
def skills_create():
    data = request.get_json()
    tool = TOOL_REGISTRY.get_tool("skills_create")
    return jsonify(tool[0](name=data["name"], description=data.get("description",""), prompt=data.get("prompt","")) if tool else {"error": "Skills not available"})


@app.route("/api/skills/<name>", methods=["DELETE"])
def skills_delete(name):
    tool = TOOL_REGISTRY.get_tool("skills_delete")
    return jsonify(tool[0](name=name) if tool else {"error": "Skills not available"})


# ======================== MEMORY ENDPOINTS ========================

@app.route("/api/memory", methods=["GET"])
def memory_list():
    tool = TOOL_REGISTRY.get_tool("memory_list")
    return jsonify(tool[0]() if tool else {"error": "Memory not available"})


@app.route("/api/memory", methods=["POST"])
def memory_write():
    data = request.get_json()
    name = data.get("name", "")
    content = data.get("content", "")
    mode = data.get("mode", "write")
    tool_name = "memory_append" if mode == "append" else "memory_write"
    tool = TOOL_REGISTRY.get_tool(tool_name)
    return jsonify(tool[0](name=name, content=content) if tool else {"error": "Memory not available"})


@app.route("/api/memory/<name>", methods=["GET"])
def memory_read(name):
    tool = TOOL_REGISTRY.get_tool("memory_read")
    return jsonify(tool[0](name=name) if tool else {"error": "Memory not available"})


@app.route("/api/memory/<name>", methods=["DELETE"])
def memory_delete(name):
    tool = TOOL_REGISTRY.get_tool("memory_delete")
    return jsonify(tool[0](name=name) if tool else {"error": "Memory not available"})


@app.route("/api/memory/search", methods=["POST"])
def memory_search():
    data = request.get_json()
    query = data.get("query", "")
    tool = TOOL_REGISTRY.get_tool("memory_search")
    return jsonify(tool[0](query=query) if tool else {"error": "Memory not available"})


# ======================== FILESYSTEM ENDPOINTS ========================

@app.route("/api/tools/shell", methods=["POST"])
def shell_exec():
    data = request.get_json()
    command = data.get("command", "")
    workdir = data.get("workdir", str(BASE_DIR))
    timeout = data.get("timeout", 30)
    tool = TOOL_REGISTRY.get_tool("bash")
    if not command:
        return jsonify({"error": "No command provided"})
    return jsonify(tool[0](command=command, workdir=str(workdir), timeout=timeout))


@app.route("/api/tools/python", methods=["POST"])
def python_exec():
    data = request.get_json()
    code = data.get("code", "")
    timeout = data.get("timeout", 30)
    tool = TOOL_REGISTRY.get_tool("python")
    return jsonify(tool[0](code=code, timeout=timeout) if tool else {"error": "Python tool not available"})


def save_conversation(user_id, last_message, reply):
    """Save a conversation turn to persistent JSON storage."""
    history = load_json(HISTORY_FILE)
    if user_id not in history:
        history[user_id] = []

    history[user_id].append({
        "id": uuid.uuid4().hex[:12],
        "user_message": last_message.get("content", "") if last_message else "",
        "assistant_reply": reply,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Keep only last 200 entries
    history[user_id] = history[user_id][-200:]
    save_json(HISTORY_FILE, history)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"  KAJUU.AI running on http://0.0.0.0:{port}")
    print(f"  API proxy: {OPENROUTER_URL}")
    app.run(host="0.0.0.0", port=port, debug=debug)

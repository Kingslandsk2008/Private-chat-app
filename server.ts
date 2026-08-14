import express from "express";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

// Serve static assets
app.use("/static", express.static(path.join(__dirname, "static")));

const DATA_DIR = path.join(__dirname, "data");
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function loadJson(filePath: string, defaultValue: any = {}) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, "utf-8"));
    }
  } catch (e) {
    console.error(`Error loading JSON from ${filePath}:`, e);
  }
  return defaultValue;
}

function saveJson(filePath: string, data: any) {
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
  } catch (e) {
    console.error(`Error saving JSON to ${filePath}:`, e);
  }
}

const DEFAULT_FREE_MODELS = [
  { id: "openrouter/free", name: "Free Router", provider: "OpenRouter", context: 128000 },
  { id: "google/gemini-2.0-flash-lite-001:free", name: "Gemini 2.0 Flash Lite", provider: "Google", context: 1048576 },
  { id: "google/gemini-2.0-pro-exp-02-05:free", name: "Gemini 2.0 Pro Exp", provider: "Google", context: 2000000 },
  { id: "deepseek/deepseek-r1:free", name: "DeepSeek R1", provider: "DeepSeek", context: 16384 },
  { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Llama 3.3 70B", provider: "Meta", context: 131072 },
  { id: "qwen/qwen-2.5-coder-32b-instruct:free", name: "Qwen 2.5 Coder 32B", provider: "Qwen", context: 32768 },
  { id: "mistralai/mistral-7b-instruct:free", name: "Mistral 7B", provider: "Mistral", context: 32768 }
];

let cachedModels = DEFAULT_FREE_MODELS;
let lastModelFetch = 0;

async function fetchFreeModels(forceRefresh = false) {
  const now = Date.now();
  if (!forceRefresh && lastModelFetch && now - lastModelFetch < 300000 && cachedModels.length) {
    return cachedModels;
  }
  try {
    const res = await fetch("https://openrouter.ai/api/v1/models", { signal: AbortSignal.timeout(10000) });
    if (res.ok) {
      const data: any = await res.json();
      const allModels = data.data || [];
      const freeModels: any[] = [];
      for (const m of allModels) {
        const pricing = m.pricing || {};
        const pCost = parseFloat(pricing.prompt || 0);
        const cCost = parseFloat(pricing.completion || 0);
        if (pCost === 0 && cCost === 0) {
          freeModels.push({
            id: m.id,
            name: m.name || m.id,
            provider: m.name?.includes(":") ? m.name.split(":")[0].trim() : m.id.split("/")[0],
            context: m.context_length || 0,
          });
        }
      }
      if (freeModels.length > 0) {
        cachedModels = freeModels;
        lastModelFetch = now;
        saveJson(path.join(DATA_DIR, "models_cache.json"), { models: freeModels, timestamp: now / 1000 });
        return cachedModels;
      }
    }
  } catch (e) {
    console.warn("Failed to fetch OpenRouter models, using default models list:", e);
  }
  return cachedModels;
}

// Serve homepage
app.get("/", (req, res) => {
  const templatePath = path.join(__dirname, "templates", "index.html");
  if (fs.existsSync(templatePath)) {
    res.sendFile(templatePath);
  } else {
    res.send("<h1>Kajuu AI</h1>");
  }
});

app.get("/api/health", (req, res) => {
  res.json({ status: "ok", version: "5.0", name: "KAJUU.AI" });
});

app.get("/api/models", async (req, res) => {
  const models = await fetchFreeModels();
  res.json({ models, count: models.length, default: "openrouter/free" });
});

app.post("/api/models/refresh", async (req, res) => {
  const models = await fetchFreeModels(true);
  res.json({ models, count: models.length });
});

// Chat Proxy Endpoint
app.post("/api/chat", async (req, res) => {
  const { user_id = "default", tab_id = "default", messages = [], model: model_key = "openrouter/free", style = "balanced", system_prompt } = req.body;

  let apiKey = process.env.OPENROUTER_API_KEY || "";
  if (!apiKey && req.headers.authorization && req.headers.authorization.startsWith("Bearer ")) {
    apiKey = req.headers.authorization.substring(7).trim();
  }
  if (!apiKey) {
    const keys = loadJson(path.join(DATA_DIR, "api_keys.json"), {});
    apiKey = keys[user_id] || "";
  }

  if (!apiKey) {
    return res.status(401).json({ error: "API key not configured. Set it in Settings." });
  }

  const model = model_key || "openrouter/free";

  let baseSystem = "You are KAJUU, a brilliant, friendly AI assistant.";
  const sysPromptFile = path.join(__dirname, "kajuu_system_prompt.md");
  if (fs.existsSync(sysPromptFile)) {
    baseSystem = fs.readFileSync(sysPromptFile, "utf-8");
  }

  const stylePrompts: Record<string, string> = {
    creative: "You are highly creative and love vivid language, unexpected analogies, and expressive descriptions.",
    balanced: "Balance creativity with precision. Be clear and engaging.",
    precise: "Be concise, accurate, and to-the-point.",
  };

  const styleInst = stylePrompts[style] || stylePrompts.balanced;
  const systemContent = system_prompt || `${baseSystem}\n\n${styleInst}`;

  const fullMessages = [{ role: "system", content: systemContent }, ...messages.slice(-100)];

  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
        "HTTP-Referer": req.headers.referer || "https://kajuu.ai",
        "X-Title": "KAJUU.AI",
      },
      body: JSON.stringify({
        model,
        max_tokens: 4096,
        temperature: style === "creative" ? 0.7 : (style === "precise" ? 0.3 : 0.5),
        messages: fullMessages,
      }),
      signal: AbortSignal.timeout(60000),
    });

    if (!response.ok) {
      const errText = await response.text();
      let errMsg = errText;
      try {
        const errJson = JSON.parse(errText);
        errMsg = errJson.error?.message || errText;
      } catch (e) {}
      return res.status(response.status).json({ error: `OpenRouter API error: ${errMsg}` });
    }

    const result: any = await response.json();
    const reply = result.choices?.[0]?.message?.content || "";

    res.json({ reply, model: result.model || model });
  } catch (error: any) {
    console.error("Chat API error:", error);
    res.status(500).json({ error: `Server error: ${error.message || error}` });
  }
});

// Chat History API
app.get("/api/history", (req, res) => {
  const userId = (req.query.user_id as string) || "default";
  const history = loadJson(path.join(DATA_DIR, "chat_history.json"), {});
  res.json(history[userId] || []);
});

app.post("/api/history", (req, res) => {
  const { user_id = "default", chats = [] } = req.body;
  const historyFile = path.join(DATA_DIR, "chat_history.json");
  const history = loadJson(historyFile, {});
  history[user_id] = chats;
  saveJson(historyFile, history);
  res.json({ status: "ok" });
});

app.delete("/api/history/:chat_id", (req, res) => {
  const userId = (req.query.user_id as string) || "default";
  const chatId = req.params.chat_id;
  const historyFile = path.join(DATA_DIR, "chat_history.json");
  const history = loadJson(historyFile, {});
  if (history[userId]) {
    history[userId] = history[userId].filter((c: any) => c.id !== chatId);
    saveJson(historyFile, history);
  }
  res.json({ status: "ok" });
});

app.post("/api/settings/apikey", (req, res) => {
  const { user_id = "default", api_key } = req.body;
  if (!api_key) return res.status(400).json({ error: "API key is required" });
  const keysFile = path.join(DATA_DIR, "api_keys.json");
  const keys = loadJson(keysFile, {});
  keys[user_id] = api_key;
  saveJson(keysFile, keys);
  res.json({ status: "ok" });
});

app.get("/api/settings/apikey", (req, res) => {
  const userId = (req.query.user_id as string) || "default";
  const keys = loadJson(path.join(DATA_DIR, "api_keys.json"), {});
  const configured = Boolean(process.env.OPENROUTER_API_KEY || keys[userId]);
  res.json({ configured });
});

// Tool mock endpoints for UI
app.get("/api/tools", (req, res) => {
  res.json({
    web_search: { description: "Search the web" },
    python: { description: "Execute Python code" },
    bash: { description: "Execute shell commands" }
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`KAJUU.AI server running at http://0.0.0.0:${PORT}`);
});

import os
from flask import Flask, request, jsonify, Response, stream_with_context
from google import genai
from google.genai import types
from tavily import TavilyClient
app = Flask(__name__)
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
def search_web(query):
    if not TAVILY_API_KEY:
        return "Tavily API key configure nahi hai."

    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

        results = []
        for item in response.get("results", []):
            results.append(
                f"Title: {item.get('title')}\n"
                f"URL: {item.get('url')}\n"
                f"Content: {item.get('content')}"
            )

        return "\n\n".join(results) if results else "Koi result nahi mila."

    except Exception as error:
        return f"Search error: {error}"
# ---------------- Settings ----------------
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
ACCESS_KEY = os.environ.get("ACCESS_KEY", "")  # optional: set this to protect /chat
MAX_MESSAGES = 40      # how many previous messages are sent as context
MAX_CHARS = 8000       # max characters per message

SYSTEM_PROMPT = (
    "You are AI 53, a smart, friendly and helpful personal AI assistant. "
    "Always reply in the same language and script the user writes in "
    "(English, Urdu, Roman Urdu, Hindi, etc.). "
    "Give clear, accurate and well-structured answers. "
    "Use Markdown: headings, bullet lists, tables and fenced code blocks "
    "with the language name when you write code. "
    "Be honest when you are not sure about something. "

    "CREATOR INFORMATION: You were created by Hafiz Subhan Ali. "
    "If anyone asks who created you, who made you, or who is your developer, "
    "say that your creator is Hafiz Subhan Ali. "
    "Instagram: https://www.instagram.com/ch_subhan53/ "
    "GitHub: https://github.com/chsubhan53 "
    "Share these links when someone asks about your creator. "
)

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            return None
        _client = genai.Client(api_key=key)
    return _client


HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 53 - Personal Assistant</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<style>
:root { --accent: #1e90ff; --cyan: #19c3ff; }
html[data-theme="dark"] {
  --bg:#050a1c; --side:#07102a; --side2:#0a2a70; --panel:#0b1736; --card:#0b1736; --box:#08122e;
  --text:#f2f6ff; --muted:#9fb0d8; --border:#1b2a58; --hover:#10204a; --user:#12306e; --glow:rgba(30,144,255,.35);
}
html[data-theme="light"] {
  --bg:#f4f7ff; --side:#ffffff; --side2:#dbe8ff; --panel:#ffffff; --card:#ffffff; --box:#ffffff;
  --text:#0b1330; --muted:#5b6a90; --border:#d5def5; --hover:#e8eefc; --user:#dbe8ff; --glow:rgba(30,144,255,.2);
}
* { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
body {
  background: var(--bg); color: var(--text); font-size: 16px;
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Noto Nastaliq Urdu", Arial, sans-serif;
}
button { font-family: inherit; color: inherit; cursor: pointer; }
.app { display: flex; height: 100vh; height: 100dvh; }

/* Sidebar */
aside {
  width: 250px; background: linear-gradient(180deg, var(--side) 0%, var(--side) 60%, var(--side2) 130%);
  display: flex; flex-direction: column; padding: 20px 16px; gap: 8px;
  border-right: 1px solid var(--border); flex-shrink: 0;
}
.brand { display:flex; align-items:center; gap:10px; font-size:24px; font-weight:700; padding: 0 4px 6px; }
.brand b { color: var(--accent); }
#newChat {
  display:flex; align-items:center; justify-content:center; gap:8px; width:100%; height:46px;
  margin-top:14px; border:0; border-radius:30px; font-size:15px; font-weight:600; color:#fff;
  background: linear-gradient(90deg,#1478ff,#1aa6ff); box-shadow: 0 0 22px var(--glow);
}
#newChat:hover { filter: brightness(1.1); }
#chatList { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:2px; margin-top:10px;
  border-top:1px solid var(--border); padding-top:12px; }
.empty-hist { color:var(--muted); font-size:14px; padding:8px 6px; display:flex; gap:10px; align-items:center; }
.chat-item {
  display:flex; align-items:center; gap:6px; padding:9px 10px; border-radius:12px;
  cursor:pointer; font-size:14px; color: var(--muted);
}
.chat-item:hover { background: var(--hover); color: var(--text); }
.chat-item.active { background: var(--panel); color: var(--text); border:1px solid var(--border); }
.chat-item .t { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.chat-item .del { opacity:0; background:none; border:0; color:var(--muted); font-size:13px; padding:2px 6px; }
.chat-item:hover .del, .chat-item.active .del { opacity:1; }
.chat-item .del:hover { color:#ff6b6b; }
.side-bottom { display:flex; flex-direction:column; gap:2px; border-top:1px solid var(--border); padding-top:12px; }
.side-btn { background:none; border:0; text-align:left; padding:10px; border-radius:10px; font-size:15px; }
.side-btn:hover { background: var(--hover); }

/* Main */
main {
  flex:1; display:flex; flex-direction:column; min-width:0;
  background:
    radial-gradient(ellipse at 92% 15%, rgba(11,58,154,.45), transparent 45%),
    radial-gradient(ellipse at 15% 0%, rgba(10,42,122,.35), transparent 40%),
    var(--bg);
}
header { display:flex; align-items:center; gap:10px; padding:16px 24px; }
header .title { font-weight:700; font-size:20px; }
header .sp { flex:1; }
header select {
  background: var(--box); color: var(--text); border:1px solid var(--border);
  border-radius:30px; padding:8px 14px; font-size:14px; outline:0;
}
#menuBtn { display:none; background:none; border:0; font-size:22px; padding:0 6px; }
#messages { flex:1; overflow-y:auto; }
.inner { max-width:800px; margin:0 auto; padding:10px 16px; }

.row { display:flex; gap:12px; margin:20px 0; }
.row.user { justify-content:flex-end; }
.bubble {
  background: var(--user); padding:10px 16px; border-radius:20px; max-width:80%;
  white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.6;
}
.avatar {
  width:30px; height:30px; border-radius:50%; flex-shrink:0; margin-top:2px;
  background: linear-gradient(135deg,#1a6fe0,#35c4f0); color:#fff;
  font-size:11px; font-weight:700; display:flex; align-items:center; justify-content:center;
}
.content { min-width:0; flex:1; }
.md { line-height:1.75; overflow-wrap:anywhere; }
.md > :first-child { margin-top:0; }
.md p { margin:.6em 0; }
.md ul, .md ol { padding-inline-start:1.5em; margin:.6em 0; }
.md li { margin:.25em 0; }
.md h1,.md h2,.md h3,.md h4 { margin:1.1em 0 .4em; line-height:1.3; }
.md a { color: var(--cyan); }
.md blockquote { margin:.8em 0; padding:.2em 1em; border-inline-start:3px solid var(--border); color:var(--muted); }
.md table { border-collapse:collapse; display:block; overflow-x:auto; margin:.8em 0; }
.md th, .md td { border:1px solid var(--border); padding:6px 12px; }
.md th { background: var(--panel); }
.md code:not(pre code) { background: var(--panel); padding:2px 6px; border-radius:6px; font-size:.9em; }
.md pre { margin:.9em 0; border-radius:12px; overflow:hidden; background:#0d1117; border:1px solid #30363d; direction:ltr; text-align:left; }
.md pre code { display:block; padding:14px 16px; overflow-x:auto; font-size:13.5px; line-height:1.6; background:transparent; }
.codebar { display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#161b22; color:#9da7b3; font-size:12px; }
.codebar button { background:none; border:0; color:#9da7b3; font-size:12px; }
.codebar button:hover { color:#fff; }
.md.typing:empty::before { content:"●"; color:var(--muted); animation: blink 1s infinite; }
@keyframes blink { 0%,100% { opacity:.2 } 50% { opacity:1 } }

.actions { display:flex; gap:4px; margin-top:6px; }
.act { background:none; border:0; color:var(--muted); font-size:12.5px; padding:4px 8px; border-radius:8px; }
.act:hover { background: var(--hover); color: var(--text); }
body.streaming .row:last-child .actions { display:none; }

/* Welcome */
.welcome { display:flex; flex-direction:column; align-items:center; text-align:center; padding-top:3vh; }
.planet { position:relative; width:220px; height:150px; margin-bottom:6px; }
.planet .orb {
  position:absolute; left:68px; top:24px; width:84px; height:84px; border-radius:50%;
  background: radial-gradient(circle at 35% 30%, #8fdcff, #1e90ff 45%, #0a3fb5 80%);
  box-shadow: 0 0 45px rgba(30,144,255,.7); animation: pulse 3s infinite ease-in-out;
}
.planet .ring {
  position:absolute; left:0; top:38px; width:220px; height:70px; border:2px solid #2a8dff;
  border-radius:50%; transform:rotate(-22deg); box-shadow:0 0 14px rgba(30,144,255,.55);
}
@keyframes pulse { 0%,100% { transform:scale(1) } 50% { transform:scale(1.06) } }
.welcome h1 { margin:0; font-size:52px; font-weight:800; letter-spacing:1px; line-height:1.1; }
.welcome h1 span { color: var(--accent); }
.welcome p { color:var(--muted); font-size:20px; font-weight:300; margin:8px 0 0; }
.welcome p b { color: var(--cyan); font-weight:400; }
.uline { width:140px; height:3px; border-radius:3px; margin:10px auto 26px;
  background: linear-gradient(90deg, transparent, #6a5cff, transparent); }
.chips { display:grid; grid-template-columns:1fr 1fr; gap:14px; width:min(760px,100%); }
.chips button {
  display:flex; align-items:center; gap:14px; min-height:68px; padding:12px 16px;
  background: var(--card); border:1px solid var(--border); border-radius:20px;
  font-size:15px; text-align:left;
}
.chips button:hover { border-color: var(--accent); box-shadow: 0 0 16px var(--glow); }
.chips .ic { font-size:26px; width:34px; text-align:center; flex-shrink:0; }
.chips .t { flex:1; }
.chips .arr { width:32px; height:32px; border-radius:50%; background: var(--hover); color:#4db3ff;
  display:flex; align-items:center; justify-content:center; flex-shrink:0; }

/* Composer */
.composer { padding:8px 16px 12px; }
.box {
  max-width:900px; margin:0 auto; display:flex; align-items:flex-end; gap:8px;
  border:2px solid transparent; border-radius:36px; padding:10px 12px 10px 24px;
  background: linear-gradient(var(--box), var(--box)) padding-box,
              linear-gradient(90deg, #19c3ff, #6a5cff) border-box;
}
textarea {
  flex:1; resize:none; border:0; outline:0; background:transparent; color:inherit;
  font:inherit; font-size:16px; line-height:1.5; max-height:200px; padding:8px 0;
}
textarea::placeholder { color: var(--muted); }
.rb { width:40px; height:40px; border-radius:50%; border:0; font-size:18px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center; background:transparent; }
.rb:hover { background: var(--hover); }
#micBtn.on { background:#ff4d4d; color:#fff; animation: blink 1s infinite; }
#sendBtn { width:48px; height:48px; color:#fff; font-size:20px;
  background: radial-gradient(circle at 30% 30%, #33c1ff, #1478ff); box-shadow: 0 0 20px var(--glow); }
#sendBtn:hover { filter:brightness(1.1); }
#sendBtn.stop { background: var(--text); color: var(--bg); box-shadow:none; }
.note { text-align:center; color:var(--muted); font-size:13px; margin-top:10px; }

#overlay { display:none; }
@media (max-width: 800px) {
  aside { position:fixed; left:0; top:0; bottom:0; z-index:30; transform:translateX(-100%); transition:transform .25s; }
  body.side-open aside { transform:none; }
  #overlay { position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:20; }
  body.side-open #overlay { display:block; }
  #menuBtn { display:inline-flex; }
  .chips { grid-template-columns:1fr; }
  .bubble { max-width:90%; }
  .welcome h1 { font-size:40px; }
  .welcome p { font-size:17px; }
  header { padding:12px 14px; }
}
</style>
</head>
<body>
<div class="app">
  <aside>
    <div class="brand">
      <svg width="40" height="34" viewBox="0 0 64 54"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4fd1ff"/><stop offset="1" stop-color="#1457ff"/></linearGradient></defs><path d="M30 2 L58 50 H44 L30 24 L16 50 H2 Z" fill="url(#lg)"/></svg>
      <span>AI <b>53</b></span>
    </div>
    <button id="newChat">＋ New chat ✎</button>
    <div id="chatList"></div>
    <div class="side-bottom">
      <button class="side-btn" id="themeBtn">🌓 Theme badlein</button>
      <button class="side-btn" id="clearAll">🗑 Saari chats delete karein</button>
    </div>
  </aside>
  <div id="overlay"></div>

  <main>
    <header>
      <button id="menuBtn" aria-label="Menu">☰</button>
      <div class="title">AI 53</div>
      <div class="sp"></div>
      <select id="voiceLang" title="Voice language">
        <option value="en-US">🌐 English</option>
        <option value="ur-PK">🌐 اردو</option>
        <option value="hi-IN">🌐 हिन्दी</option>
      </select>
    </header>

    <div id="messages"><div class="inner" id="inner"></div></div>

    <div class="composer">
      <div class="box">
        <textarea id="input" rows="1" dir="auto" placeholder="AI se kuch bhi poochhein..."></textarea>
        <button class="rb" id="micBtn" title="Voice input">🎙️</button>
        <button class="rb" id="sendBtn" title="Send">➤</button>
      </div>
      <div class="note">🛡 AI 53 aapki har tarah ki madad ke liye yahan hai. Zaroori maloomat dobara check karein.</div>
    </div>
  </main>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
(() => {
  const $ = s => document.querySelector(s);
  const inner = $("#inner"), scroller = $("#messages"), input = $("#input");
  const sendBtn = $("#sendBtn"), micBtn = $("#micBtn");
  const KEY = "ai53_chats_v2", CUR = "ai53_current_v2";
  const SUGGESTIONS = [
    { i: "✦", t: "Mujhe Python code kaise likhna hai?" },
    { i: "💡", t: "Ek chhota sa kahani sunao" },
    { i: "📊", t: "Professional email likhne mein madad karo" },
    { i: "🎨", t: "Mere liye creative design banayein" }
  ];

  let chats = [];
  try { chats = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { chats = []; }
  let currentId = localStorage.getItem(CUR) || null;
  let streaming = false, controller = null;

  const save = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify(chats));
      localStorage.setItem(CUR, currentId || "");
    } catch {}
  };
  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const cur = () => chats.find(c => c.id === currentId);
  if (!cur()) currentId = null;

  /* ---------- Theme & sidebar ---------- */
  const applyTheme = t => {
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem("ai53_theme", t); } catch {}
  };
  applyTheme(localStorage.getItem("ai53_theme") || "dark");
  $("#themeBtn").onclick = () =>
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

  const openSide = v => document.body.classList.toggle("side-open", v);
  $("#menuBtn").onclick = () => openSide(true);
  $("#overlay").onclick = () => openSide(false);

  /* ---------- Markdown ---------- */
  if (window.marked) marked.setOptions({ breaks: true, gfm: true });
  if (window.DOMPurify) {
    DOMPurify.addHook("afterSanitizeAttributes", node => {
      if (node.tagName === "A") {
        node.setAttribute("target", "_blank");
        node.setAttribute("rel", "noopener noreferrer");
      }
    });
  }

  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch {}
      ta.remove();
    }
  }

  function setMd(el, text) {
    if (!text) { el.textContent = ""; return; }
    if (!window.marked || !window.DOMPurify) {
      el.textContent = text; el.style.whiteSpace = "pre-wrap"; return;
    }
    el.innerHTML = DOMPurify.sanitize(marked.parse(text));
    el.querySelectorAll("pre").forEach(pre => {
      const code = pre.querySelector("code");
      if (!code) return;
      try { if (window.hljs) hljs.highlightElement(code); } catch {}
      const cls = [...code.classList].find(c => c.startsWith("language-"));
      const lang = cls ? cls.replace("language-", "") : "code";
      const bar = document.createElement("div");
      bar.className = "codebar";
      const label = document.createElement("span");
      label.textContent = lang;
      const btn = document.createElement("button");
      btn.textContent = "Copy";
      btn.onclick = async () => {
        await copyText(code.innerText);
        btn.textContent = "Copied ✓";
        setTimeout(() => (btn.textContent = "Copy"), 1500);
      };
      bar.append(label, btn);
      pre.prepend(bar);
    });
  }

  /* ---------- Rendering ---------- */
  function actBtn(label, fn) {
    const b = document.createElement("button");
    b.className = "act"; b.textContent = label;
    b.onclick = () => fn(b);
    return b;
  }
  const flash = (b, t) => {
    const old = b.textContent; b.textContent = t;
    setTimeout(() => (b.textContent = old), 1500);
  };

  function speak(text) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = $("#voiceLang").value;
    speechSynthesis.speak(u);
  }

  function rowEl(m, isLast) {
    const row = document.createElement("div");
    row.className = "row " + m.role;
    if (m.role === "user") {
      const b = document.createElement("div");
      b.className = "bubble"; b.dir = "auto"; b.textContent = m.text;
      row.appendChild(b);
      return row;
    }
    const av = document.createElement("div"); av.className = "avatar"; av.textContent = "53";
    const ct = document.createElement("div"); ct.className = "content";
    const md = document.createElement("div"); md.className = "md"; md.dir = "auto";
    setMd(md, m.text);
    const act = document.createElement("div"); act.className = "actions";
    act.append(
      actBtn("Copy", async b => { await copyText(m.text); flash(b, "Copied ✓"); }),
      actBtn("Speak", () => speak(md.innerText))
    );
    if (isLast) act.append(actBtn("Regenerate", () => regenerate()));
    ct.append(md, act);
    row.append(av, ct);
    return row;
  }

  function welcome() {
    const d = document.createElement("div");
    d.className = "welcome";
    d.innerHTML =
      '<div class="planet"><div class="orb"></div><div class="ring"></div></div>' +
      '<h1>AI <span>53</span></h1>' +
      '<p>Main aapki kaise <b>madad</b> kar sakta hoon?</p>' +
      '<div class="uline"></div><div class="chips"></div>';
    const chips = d.querySelector(".chips");
    SUGGESTIONS.forEach(s => {
      const b = document.createElement("button");
      b.innerHTML = '<span class="ic"></span><span class="t"></span><span class="arr">→</span>';
      b.querySelector(".ic").textContent = s.i;
      b.querySelector(".t").textContent = s.t;
      b.onclick = () => send(s.t);
      chips.appendChild(b);
    });
    return d;
  }

  function renderAll() {
    inner.innerHTML = "";
    const c = cur();
    if (!c || !c.messages.length) { inner.appendChild(welcome()); return; }
    c.messages.forEach((m, i) => inner.appendChild(rowEl(m, i === c.messages.length - 1)));
    scroller.scrollTop = scroller.scrollHeight;
  }

  function renderList() {
    const list = $("#chatList");
    list.innerHTML = "";
    if (!chats.length) {
      const e = document.createElement("div");
      e.className = "empty-hist";
      e.textContent = "🕘 Abhi koi chat history nahi...";
      list.appendChild(e);
      return;
    }
    [...chats].sort((a, b) => b.updated - a.updated).forEach(c => {
      const item = document.createElement("div");
      item.className = "chat-item" + (c.id === currentId ? " active" : "");
      const t = document.createElement("span");
      t.className = "t"; t.dir = "auto"; t.textContent = c.title || "New chat";
      const del = document.createElement("button");
      del.className = "del"; del.title = "Delete"; del.textContent = "✕";
      del.onclick = e => { e.stopPropagation(); deleteChat(c.id); };
      item.onclick = () => {
        if (streaming) return;
        currentId = c.id; save(); renderList(); renderAll(); openSide(false);
      };
      item.append(t, del);
      list.appendChild(item);
    });
  }

  function deleteChat(id) {
    if (streaming) return;
    chats = chats.filter(c => c.id !== id);
    if (currentId === id) currentId = null;
    save(); renderList(); renderAll();
  }

  /* ---------- Chat logic ---------- */
  function setBtn(busy) {
    sendBtn.textContent = busy ? "■" : "➤";
    sendBtn.title = busy ? "Stop" : "Send";
    sendBtn.classList.toggle("stop", busy);
  }

  function send(text) {
    if (streaming) return;
    text = (text || "").trim();
    if (!text) return;
    let c = cur();
    if (!c) {
      c = { id: uid(), title: "New chat", messages: [], updated: Date.now() };
      chats.push(c); currentId = c.id;
    }
    if (!c.messages.length) c.title = text.replace(/\s+/g, " ").slice(0, 40);
    c.messages.push({ role: "user", text }, { role: "assistant", text: "" });
    c.updated = Date.now();
    save(); renderList(); renderAll();
    generate(c);
  }

  function regenerate() {
    const c = cur();
    if (streaming || !c) return;
    const last = c.messages[c.messages.length - 1];
    if (!last || last.role !== "assistant") return;
    last.text = "";
    renderAll();
    generate(c);
  }

  async function generate(chat) {
    streaming = true;
    document.body.classList.add("streaming");
    setBtn(true);
    controller = new AbortController();

    const last = chat.messages[chat.messages.length - 1];
    const history = chat.messages.slice(0, -1).map(m => ({ role: m.role, text: m.text }));
    const mdEl = inner.lastElementChild.querySelector(".md");
    mdEl.classList.add("typing");

    let raf = 0;
    const scheduleRender = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const near = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 150;
        setMd(mdEl, last.text);
        if (near) scroller.scrollTop = scroller.scrollHeight;
      });
    };

    try {
      const headers = { "Content-Type": "application/json" };
      const k = localStorage.getItem("ai53_key");
      if (k) headers["X-Access-Key"] = k;

      const res = await fetch("/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({ messages: history }),
        signal: controller.signal
      });

      if (!res.ok) {
        let msg = "Server error (" + res.status + ")";
        try { msg = (await res.json()).error || msg; } catch {}
        if (res.status === 401) {
          const nk = prompt("Access key likhein:");
          if (nk) localStorage.setItem("ai53_key", nk);
          msg += " Key save ho gayi, ab Regenerate dabayein.";
        }
        throw new Error(msg);
      }

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        last.text += dec.decode(value, { stream: true });
        scheduleRender();
      }
      last.text += dec.decode();
    } catch (err) {
      if (err.name === "AbortError") {
        if (!last.text) last.text = "_(Jawab rok diya gaya)_";
      } else {
        last.text += (last.text ? "\n\n" : "") + "⚠️ " + err.message;
      }
    } finally {
      mdEl.classList.remove("typing");
      setMd(mdEl, last.text);
      chat.updated = Date.now();
      save(); renderList();
      streaming = false; controller = null;
      document.body.classList.remove("streaming");
      setBtn(false);
      input.focus();
    }
  }

  /* ---------- Input ---------- */
  const autosize = () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  };
  input.addEventListener("input", autosize);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      if (!streaming) doSend();
    }
  });

  function doSend() {
    const t = input.value;
    if (!t.trim()) return;
    input.value = ""; autosize();
    send(t);
  }

  sendBtn.onclick = () => (streaming ? controller && controller.abort() : doSend());

  $("#newChat").onclick = () => {
    if (streaming) return;
    currentId = null; save(); renderList(); renderAll(); openSide(false); input.focus();
  };
  $("#clearAll").onclick = () => {
    if (streaming) return;
    if (!confirm("Kya aap saari chats delete karna chahte hain?")) return;
    chats = []; currentId = null; save(); renderList(); renderAll();
  };

  /* ---------- Voice input ---------- */
  let rec = null;
  micBtn.onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Is browser mein voice input available nahi hai. Chrome use karein."); return; }
    if (rec) { rec.stop(); return; }
    rec = new SR();
    rec.lang = $("#voiceLang").value;
    rec.interimResults = true;
    micBtn.classList.add("on");
    const base = input.value;
    rec.onresult = e => {
      let t = "";
      for (const r of e.results) t += r[0].transcript;
      input.value = (base ? base + " " : "") + t;
      autosize();
    };
    rec.onerror = () => {};
    rec.onend = () => { micBtn.classList.remove("on"); rec = null; input.focus(); };
    rec.start();
  };

  /* ---------- Init ---------- */
  renderList();
  renderAll();
  input.focus();
})();
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return Response(HTML, mimetype="text/html")


@app.route("/chat", methods=["POST"])
def chat():
    if ACCESS_KEY and request.headers.get("X-Access-Key", "") != ACCESS_KEY:
        return jsonify({"error": "Access key galat ya missing hai."}), 401

    data = request.get_json(silent=True) or {}
    msgs = data.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return jsonify({"error": "Message khali hai."}), 400

    # Build conversation for Gemini (server stays stateless)
    contents = []
    for m in msgs[-MAX_MESSAGES:]:
        if not isinstance(m, dict):
            continue
        text = str(m.get("text", "")).strip()[:MAX_CHARS]
        if not text:
            continue
        role = "user" if m.get("role") == "user" else "model"
        if contents and contents[-1].role == role:
            contents[-1].parts[0].text += "\n\n" + text
            continue
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

    while contents and contents[0].role != "user":
        contents.pop(0)
    if not contents or contents[-1].role != "user":
        return jsonify({"error": "Message khali hai."}), 400

    client = get_client()
    if client is None:
        return jsonify({"error": "GEMINI_API_KEY configure nahi hai."}), 500

    def generate():
        try:
            # User ka latest message
            user_query = contents[-1].parts[0].text

            # Internet search ki zaroorat check karo
            search_words = [
                # English
                "search", "internet", "latest", "today",
                "current", "news", "price", "weather",
                "recent", "update", "updates", "2026",
                "right now", "at the moment",
                "live", "breaking", "release", "launched",
                "exchange rate", "stock price",

                # Roman Urdu
                "aaj", "abhi", "taaza", "taza",
                "khabar", "qeemat", "keemat",
                "kitne ka", "kitni hai", "rate kya",
                "price kya", "naya update",
                "nayi khabar", "kya hua",
                "maloomat dhoondo", "pata karo",
                "internet se", "search karo",
                "check karo", "dhoond kar batao"
            ]

            system_prompt = SYSTEM_PROMPT

            if any(word in user_query.lower() for word in search_words):
                search_results = search_web(user_query)

                system_prompt += (
                    "\n\nWEB SEARCH RESULTS:\n"
                    + search_results
                    + "\n\nUse these search results to answer accurately. "
                    "Include relevant source URLs in your answer. "
                    "If results are insufficient, say so honestly."
                )

            stream = client.models.generate_content_stream(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.8,
                ),
            )

            got = False
            for chunk in stream:
                text = chunk.text
                if text:
                    got = True
                    yield text

            if not got:
                yield "Koi jawab nahi mila."

        except Exception as error:
            yield "\n\nAI error: " + str(error)

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

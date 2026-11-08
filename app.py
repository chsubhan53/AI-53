
import os
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

MODEL = "gemini-3.5-flash-lite"
client = None

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 53 - Personal Assistant</title>
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    color: #eaf4ff;
    background:
      radial-gradient(ellipse at 50% 0%, #102d58 0%, transparent 55%),
      #050b18;
    min-height: 100vh;
}

.container {
    max-width: 900px;
    margin: auto;
    padding: 25px 18px;
}

header {
    text-align: center;
    padding: 20px 0 25px;
}

.logo {
    font-size: 38px;
    font-weight: bold;
    letter-spacing: 5px;
    color: #75caff;
    text-shadow: 0 0 15px #168cff, 0 0 35px #087bff;
}

.subtitle {
    color: #8ba9c9;
    font-size: 13px;
    letter-spacing: 3px;
    margin-top: 9px;
}

.orb-area {
    display: flex;
    justify-content: center;
    padding: 10px 0 25px;
}

.orb {
    width: 105px;
    height: 105px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%,
       #ffffff, #63c9ff 18%, #1769d8 48%, #061b4b 75%);
    box-shadow: 0 0 20px #168bff,
                0 0 45px #087bff,
                inset 0 0 20px #b7eaff;
    animation: pulse 3s infinite ease-in-out;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); box-shadow: 0 0 20px #168bff, 0 0 45px #087bff; }
    50% { transform: scale(1.07); box-shadow: 0 0 30px #36baff, 0 0 65px #087bff; }
}

.status {
    text-align: center;
    color: #59d9ff;
    font-size: 12px;
    letter-spacing: 2px;
    margin-bottom: 18px;
}

.chat {
    height: 48vh;
    min-height: 300px;
    overflow-y: auto;
    padding: 18px;
    border: 1px solid #174a78;
    border-radius: 18px;
    background: rgba(9, 22, 43, .88);
    box-shadow: 0 0 25px rgba(0, 125, 255, .12);
}

.message {
    padding: 13px 16px;
    margin: 12px 0;
    border-radius: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.user {
    background: linear-gradient(120deg, #123d72, #125c9c);
    border: 1px solid #277fca;
    margin-left: 12%;
}

.bot {
    background: #101f36;
    border: 1px solid #1c527b;
    margin-right: 12%;
}

.controls {
    display: flex;
    gap: 10px;
    margin-top: 16px;
}

input {
    flex: 1;
    min-width: 0;
    padding: 16px;
    border: 1px solid #235c8c;
    border-radius: 12px;
    outline: none;
    background: #0b1830;
    color: white;
    font-size: 15px;
}

input:focus {
    border-color: #42baff;
    box-shadow: 0 0 12px #087bff55;
}

button {
    padding: 14px 23px;
    border: 0;
    border-radius: 12px;
    color: white;
    font-weight: bold;
    cursor: pointer;
    background: linear-gradient(120deg, #087bff, #20b9ed);
    box-shadow: 0 0 15px #087bff66;
}

button:disabled {
    opacity: .5;
    cursor: wait;
}

.footer {
    text-align: center;
    color: #56728f;
    font-size: 11px;
    margin-top: 22px;
    letter-spacing: 1px;
}

@media(max-width: 600px) {
    .container { padding: 12px; }
    .chat { height: 52vh; }
    .user { margin-left: 5%; }
    .bot { margin-right: 5%; }
    button { padding: 13px 16px; }
}
</style>
</head>

<body>
<div class="container">
<header>
    <div class="logo">AI 53</div>
    <div class="subtitle">YOUR PERSONAL AI ASSISTANT</div>
</header>

<div class="orb-area">
    <div class="orb"></div>
</div>

<div class="status">● AI SYSTEM ONLINE</div>

<div class="chat" id="chat">
    <div class="message bot">
        53: Hello! Main aapka AI assistant hoon.
        Aap mujhse kuch bhi pooch sakte hain.
    </div>
</div>

<div class="controls">
    <input id="message" placeholder="Ask AI 53 anything..."
      onkeydown="if(event.key==='Enter') sendMessage()">
    <button id="send" onclick="sendMessage()">SEND ➤</button>
</div>

<div class="footer">POWERED BY GEMINI · AI 53</div>
</div>

<script>
let previousId = null;

async function sendMessage() {
    const input = document.getElementById("message");
    const chat = document.getElementById("chat");
    const button = document.getElementById("send");
    const message = input.value.trim();

    if (!message || button.disabled) return;

    const user = document.createElement("div");
    user.className = "message user";
    user.textContent = "You: " + message;
    chat.appendChild(user);

    input.value = "";

    const loading = document.createElement("div");
    loading.className = "message bot";
    loading.textContent = "53: Soch raha hoon...";
    chat.appendChild(loading);

    button.disabled = true;
    chat.scrollTop = chat.scrollHeight;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: message,
                previous_id: previousId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "AI response error");
        }

        loading.textContent = "53: " + (data.reply || "Koi jawab nahi mila.");

        if (data.id) previousId = data.id;

    } catch (error) {
        loading.textContent = "53: " + error.message;
    } finally {
        button.disabled = false;
        input.focus();
        chat.scrollTop = chat.scrollHeight;
    }
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    global client

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    previous_id = data.get("previous_id")

    if not message:
        return jsonify({"error": "Message khali hai."}), 400

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API key configure nahi hai."}), 500

    try:
        if client is None:
            client = genai.Client(api_key=api_key)

        options = {
            "model": MODEL,
            "input": message
        }

        if previous_id:
            options["previous_interaction_id"] = previous_id

        result = client.interactions.create(**options)

        return jsonify({
            "reply": result.output_text or "Koi jawab nahi mila.",
            "id": result.id
        })

    except Exception as error:
        return jsonify({"error": "AI error: " + str(error)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

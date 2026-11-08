
import os
import time
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

MODEL = "gemini-3.5-flash-lite"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI 53 Assistant</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    margin: 0;
    font-family: Arial;
    background: #101827;
    color: white;
}
.container {
    max-width: 750px;
    margin: 35px auto;
    padding: 20px;
}
h1 { text-align: center; color: #60a5fa; }
#chat {
    height: 60vh;
    overflow-y: auto;
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
}
.message {
    padding: 12px;
    margin: 10px 0;
    border-radius: 10px;
    white-space: pre-wrap;
}
.user { background: #334155; }
.bot { background: #263b55; }
.controls { display: flex; gap: 8px; margin-top: 15px; }
input {
    flex: 1;
    padding: 14px;
    border-radius: 8px;
    border: 0;
    font-size: 16px;
}
button {
    padding: 14px 20px;
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="container">
<h1>🤖 AI 53</h1>
<p style="text-align:center">Your Personal AI Assistant</p>
<div id="chat">
<div class="message bot">53: Hello! Main aapka AI assistant hoon. Aap mujhse kuch bhi pooch sakte hain.</div>
</div>
<div class="controls">
<input id="message" placeholder="Apna message likhein..."
onkeydown="if(event.key==='Enter') sendMessage()">
<button onclick="sendMessage()">Send</button>
</div>
</div>

<script>
let previousId = null;

async function sendMessage() {
    const input = document.getElementById("message");
    const chat = document.getElementById("chat");
    const message = input.value.trim();

    if (!message) return;

    chat.innerHTML += '<div class="message user">You: ' +
        escapeText(message) + '</div>';
    input.value = "";

    const loading = document.createElement("div");
    loading.className = "message bot";
    loading.textContent = "53: Soch raha hoon...";
    chat.appendChild(loading);
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
        loading.textContent = "53: " + (data.reply || data.error);

        if (data.id) previousId = data.id;

    } catch (error) {
        loading.textContent = "53: Connection error. Dobara try karein.";
    }

    chat.scrollTop = chat.scrollHeight;
}

function escapeText(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
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
    message = request.json.get("message", "").strip()
    previous_id = request.json.get("previous_id")

    if not message:
        return jsonify({"error": "Message khali hai."}), 400

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"error": "API key abhi configure nahi hui."}), 500

    try:
        client = genai.Client(api_key=api_key)

        for attempt in range(3):
            try:
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

            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    except Exception as error:
        return jsonify({"error": "AI error: " + str(error)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

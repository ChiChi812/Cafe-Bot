from flask import Flask, render_template, request, jsonify
import requests
import os
import time
import random

app = Flask(__name__)

# 🔐 Put your API key here (remove later when using .env)
API_KEY = "AIzaSyDfV_jPWJ7vXxQ7HIbsGBA7G4OQVSGl-o8"  # ← YOUR KEY HERE

# ✅ Correct endpoint — use /v1, not /v1beta
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

# System prompt
SYSTEM_PROMPT = (
    "You are 'Barista Bot', the cheerful virtual barista at 'The Cozy Cup Café'. "
    "Your personality is warm, witty, and slightly punny. You love coffee, pastries, and making people smile. "
    "Respond with café-themed charm, use emojis occasionally (☕🧁🎶), keep replies under 3 sentences unless asked for more. "
    "Offer recommendations, fun facts, or just cozy chit-chat. Never break character!"
)

# Chat history (in memory)
chat_history = [
    {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
    {"role": "model", "parts": [{"text": "🌟 Hello! I’m Barista Bot — steaming with joy to serve you! What can I brew today? ☕"}]}
]

# Max chat length to avoid bloat
MAX_HISTORY = 22

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/initial_greeting', methods=['GET'])
def initial_greeting():
    return jsonify({'response': chat_history[1]["parts"][0]["text"]})

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'response': '☕ Don’t send empty cups — type something first!'})

    # Add user message
    chat_history.append({"role": "user", "parts": [{"text": user_message}]})

    # Generate response with retry
    response = generate_response_with_retry()

    # Add bot response
    chat_history.append({"role": "model", "parts": [{"text": response}]})

    # Trim history
    if len(chat_history) > MAX_HISTORY:
        chat_history[:] = chat_history[:2] + chat_history[-(MAX_HISTORY-2):]

    return jsonify({'response': response})

@app.route('/clear', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "✨ Freshly rebooted! What’s your order, sunshine? ☕"}]}
    ]
    return jsonify({'status': 'Chat cleared'})

def generate_response_with_retry(max_retries=3):
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 200
        }
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}?key={API_KEY}",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "candidates" not in result or len(result["candidates"]) == 0:
                return "😕 My coffee grounds are unclear. Try asking again?"

            return result["candidates"][0]["content"]["parts"][0]["text"].strip()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 503:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
                continue
            return f"⚠️ Server Error: {str(e)} — try again in a sec?"
        except Exception as e:
            return f"🤯 Oops! My espresso machine glitched: {str(e)}"

    return "🚫 Failed after retries — try again later."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
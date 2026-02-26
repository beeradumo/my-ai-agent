import os
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# Configurare Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/webhook', methods=['POST'])
def handle_message():
    data = request.json
    user_message = data.get('message')

    # Trimite la Gemini
    response = model.generate_content(f"Acționează ca un asistent personal. Mesaj: {user_message}")

    return {"status": "success", "reply": response.text}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

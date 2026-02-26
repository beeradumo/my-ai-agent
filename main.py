import os
from flask import Flask, send_file, render_template_string, request
import google.generativeai as genai
import qrcode
from io import BytesIO

app = Flask(__name__)

# Config Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def home():
    return "Server AI Activ!"

@app.route('/login')
def login():
    # Simulăm generarea QR-ului pentru WhatsApp
    # (Aici vei integra librăria de WA după ce trecem de build)
    return "<h1>Scanează QR (Placeholder)</h1><img src='/get-qr'>"

@app.route('/get-qr')
def get_qr():
    qr = qrcode.make("https://wa.me/your-number") # De test
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    msg = data.get("text", "")
    response = model.generate_content(f"Ești asistentul meu. Răspunde la: {msg}")
    return {"reply": response.text}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

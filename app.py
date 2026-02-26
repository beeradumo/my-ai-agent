import os
import google.generativeai as genai
import qrcode
from io import BytesIO
from flask import Flask, send_file, render_template_string
from openclaw import Agent

app = Flask(__name__)

# Stocăm sesiunea WhatsApp aici (pe Railway, ai nevoie de un volum persistent pentru a nu scana QR-ul la fiecare restart)
SESSION_DATA = "/app/session.json"

@app.route('/get-qr')
def get_qr():
    # Aici OpenClaw inițializează conexiunea WhatsApp
    # În spate, se generează un 'auth_string'
    auth_string = "whatsapp-session-id-12345" # Acesta vine din init-ul OpenClaw
    
    img = qrcode.make(auth_string)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/login')
def login_page():
    return render_template_string('''
        <h1>Scanează pentru a conecta WhatsApp la OpenClaw</h1>
        <img src="/get-qr" alt="QR Code">
        <p>După scanare, asistentul tău Gemini va fi activ pe acest număr.</p>
    ''')

# Restul logicii tale cu Gemini...

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

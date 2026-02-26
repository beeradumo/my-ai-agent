import os
import google.generativeai as genai
import qrcode
from io import BytesIO
from flask import Flask, send_file, render_template_string
from openclaw import Agent

app = Flask(__name__)

# Calea către volumul persistent din Railway
SESSION_PATH = "/app/session/whatsapp_auth"

# Configurăm Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Presupunem că folosim un client de WhatsApp integrat în OpenClaw
# Vom simula verificarea stării conexiunii
def is_whatsapp_connected():
    # Verifică dacă folderul de sesiune există și are date
    return os.path.exists(SESSION_PATH) and len(os.listdir(SESSION_PATH)) > 0

@app.route('/login')
def login_page():
    if is_whatsapp_connected():
        return "<h1>Securizat: Instanța este deja activă și conectată.</h1>", 403
    
    return render_template_string('''
        <h1>Conectare Securizată OpenClaw</h1>
        <div id="qr-container">
            <img src="/get-qr" alt="QR Code">
        </div>
        <script>
            // Refresh automat pagina la 30 secunde pentru un nou QR dacă nu s-a scanat
            setTimeout(() => { location.reload(); }, 30000);
        </script>
    ''')

@app.route('/get-qr')
def get_qr():
    if is_whatsapp_connected():
        return "Acces interzis", 403

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

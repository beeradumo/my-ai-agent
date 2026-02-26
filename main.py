import os
import sys
import time
import qrcode
from io import BytesIO
from flask import Flask, send_file, render_template_string, request, jsonify

# --- 1. Încercare Import OpenClaw (Adaptiv pentru Linux/Railway) ---
try:
    import openclaw
    # Încercăm cele mai comune structuri de import pentru framework-ul de agenți
    if hasattr(openclaw, 'Agent'):
        from openclaw import Agent
    else:
        from openclaw.agents import Agent
    print("✅ Framework-ul OpenClaw a fost încărcat corect!")
except ImportError as e:
    print(f"❌ Eroare critică de import: {e}")
    sys.exit(1)

import google.generativeai as genai

# --- 2. Configurare Aplicație și Securitate ---
app = Flask(__name__)

# Calea către volumul persistent din Railway (trebuie să-l creezi în Dashboard)
SESSION_PATH = "/app/session/whatsapp_auth"
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "claw123") # Parola pentru QR

# Configurare Gemini 1.5 Free
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. Logica de Verificare Conexiune ---
def is_connected():
    # Dacă există fișiere de sesiune în volum, înseamnă că suntem logați
    return os.path.exists(SESSION_PATH) and len(os.listdir(SESSION_PATH)) > 0

# --- 4. Rutele pentru WhatsApp QR Code ---
@app.route('/login')
def login():
    token = request.args.get("token")
    if token != ADMIN_TOKEN:
        return "<h1>Acces Neautorizat</h1><p>Adaugă ?token=parola ta în URL.</p>", 401
    
    if is_connected():
        return "<h1>Status: Conectat</h1><p>WhatsApp este deja activ.</p>"

    return render_template_string('''
        <html>
            <head><title>OpenClaw Login</title></head>
            <body style="text-align: center; font-family: sans-serif; padding-top: 50px;">
                <h1>Scanează Codul QR pentru WhatsApp</h1>
                <div style="margin: 20px auto; border: 5px solid #333; display: inline-block;">
                    <img src="/get-qr?token={{token}}" alt="QR Code" style="width: 300px;">
                </div>
                <p>Odată scanat, asistentul tău AI va prelua mesajele.</p>
                <script>setTimeout(function(){ location.reload(); }, 20000);</script>
            </body>
        </html>
    ''', token=token)

@app.route('/get-qr')
def get_qr():
    token = request.args.get("token")
    if token != ADMIN_TOKEN or is_connected():
        return "Forbidden", 403

    # Generăm un placeholder pentru QR (OpenClaw va furniza string-ul real de auth)
    # În producție, aici vei integra funcția agent.get_whatsapp_qr()
    qr_data = "OPENCLAW_AUTH_STRING_PLACEHOLDER" 
    
    img = qrcode.make(qr_data)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# --- 5. Logica de Procesare Mesaje (Brain-ul) ---
def handle_ai_logic(incoming_msg):
    """
    Funcția care decide ce să facă cu un mesaj primit.
    """
    prompt = f"Ești un asistent personal pe WhatsApp. Răspunde în română la: {incoming_msg}"
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Eroare AI: {str(e)}"

# --- 6. Pornirea Serverului ---
@app.route('/')
def health_check():
    status = "Conectat" if is_connected() else "Așteaptă Login"
    return jsonify({"service": "OpenClaw AI", "status": status})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 OpenClaw Agent pornește pe portul {port}...")
    app

import os
import qrcode
import google.generativeai as genai
from flask import Flask, send_file, render_template_string, request
from io import BytesIO

app = Flask(__name__)

# Configurare Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Variabilă globală pentru a stoca ultimul string QR primit de la bridge
# În pasul următor, vom conecta un bridge real
current_qr_string = None 

@app.route('/')
def home():
    return "<h1>Server AI Online</h1><p>Mergi la /login pentru WhatsApp.</p>"

@app.route('/login')
def login():
    return render_template_string('''
        <html>
            <body style="text-align: center; font-family: sans-serif; background: #f0f2f5;">
                <div style="margin-top: 50px; background: white; display: inline-block; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2>Conectează WhatsApp la Gemini</h2>
                    <img src="/get-qr" style="width: 300px; border: 1px solid #ccc;">
                    <p>Deschide WhatsApp > Dispozitive conectate > Conectați un dispozitiv</p>
                    <button onclick="location.reload()" style="padding: 10px 20px; cursor: pointer;">Reîmprospătează QR</button>
                </div>
                <script>setTimeout(() => location.reload(), 15000);</script>
            </body>
        </html>
    ''')

@app.route('/get-qr')
def get_qr():
    # AICI ESTE SECRETUL: Pentru a fi scanabil, codul QR trebuie să conțină 
    # un string de tip '2@...'. Dacă folosim un URL simplu, WhatsApp dă eroare.
    
    # Placeholder pentru string-ul real de la serverul de WA
    # Pentru testare, dacă nu ai bridge-ul activ, telefonul va da eroare.
    qr_auth_data = os.environ.get("LAST_QR_STR", "INV-QR-CODE") 
    
    img = qrcode.make(qr_auth_data)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

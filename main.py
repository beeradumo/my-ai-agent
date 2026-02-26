import os
import subprocess
import threading
import time
from flask import Flask, render_template_string, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Config Gemini
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

pairing_code = "Așteaptă..."
bot_status = "Se generează codul..."
PHONE_NUMBER = "40753873825" # !!! PUNE AICI NUMĂRUL TĂU CU PREFIX (ex: 40722123456)

def run_wa_bridge():
    global pairing_code, bot_status
    
    node_code = f"""
    const {{ default: makeWASocket, useMultiFileAuthState, delay }} = require('@whiskeysockets/baileys');
    const pino = require('pino');

    async function connect() {{
        const {{ state, saveCreds }} = await useMultiFileAuthState('auth_session');
        const sock = makeWASocket({{
            auth: state,
            printQRInTerminal: false,
            logger: pino({{ level: 'silent' }}),
            browser: ["Ubuntu", "Chrome", "110.0.5481.177"]
        }});

        if (!sock.authState.creds.registered) {{
            console.log('REQUESTING_CODE');
            await delay(3000);
            const code = await sock.requestPairingCode('{PHONE_NUMBER}');
            console.log('PAIRING_CODE:' + code);
        }}

        sock.ev.on('creds.update', saveCreds);
        sock.ev.on('connection.update', (update) => {{
            const {{ connection }} = update;
            if (connection === 'open') console.log('STATUS:CONNECTED');
            if (connection === 'close') connect();
        }});
    }}
    connect();
    """
    
    with open("bridge.js", "w") as f: f.write(node_code)
    process = subprocess.Popen(["node", "bridge.js"], stdout=subprocess.PIPE, text=True)

    for line in process.stdout:
        line = line.strip()
        if "PAIRING_CODE:" in line:
            pairing_code = line.split(":")[1]
            bot_status = "Cod Generat!"
        elif "STATUS:CONNECTED" in line:
            bot_status = "CONECTAT"
            pairing_code = "CONECTAT"

threading.Thread(target=run_wa_bridge, daemon=True).start()

@app.route('/login')
def login():
    return render_template_string('''
        <body style="text-align: center; font-family: sans-serif; padding-top: 50px; background: #f0f2f5;">
            <div style="background: white; display: inline-block; padding: 30px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <h2>Conectare prin Cod</h2>
                <p>Status: <strong>{{status}}</strong></p>
                {% if code != "CONECTAT" %}
                    <div style="font-size: 3em; letter-spacing: 10px; font-weight: bold; color: #25D366; margin: 20px 0;">
                        {{code}}
                    </div>
                    <p>1. Deschide WhatsApp pe telefon</p>
                    <p>2. Dispozitive conectate -> Conectați un dispozitiv</p>
                    <p>3. Apasă <strong>"Conectați folosind numărul de telefon"</strong></p>
                    <p>4. Introdu codul de mai sus</p>
                {% else %}
                    <h2 style="color: green;">✅ Ești conectat!</h2>
                {% endif %}
            </div>
            <script>setTimeout(() => location.reload(), 10000);</script>
        </body>
    ''', status=bot_status, code=pairing_code)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

import os
import subprocess
import threading
import time
from flask import Flask, render_template_string

app = Flask(__name__)

# --- CONFIGURARE ---
# PUNE NUMĂRUL TĂU AICI (Exemplu: 40722111222)
MY_PHONE = "40753873825" 

pairing_code = "Se generează..."
bot_status = "Inițializare..."

def run_wa_bridge():
    global pairing_code, bot_status
    
    # Scriptul Node.js forțat să ceară Pairing Code
    node_code = f"""
    const {{ default: makeWASocket, useMultiFileAuthState, delay, fetchLatestBaileysVersion }} = require('@whiskeysockets/baileys');
    const pino = require('pino');

    async function connect() {{
        // IMPORTANT: Folosim un folder nou de sesiune pentru a evita conflictele
        const {{ state, saveCreds }} = await useMultiFileAuthState('auth_session_new');
        const {{ version }} = await fetchLatestBaileysVersion();

        const sock = makeWASocket({{
            version,
            auth: state,
            printQRInTerminal: false,
            logger: pino({{ level: 'silent' }}),
            // Identificare ca browser Desktop pentru a permite pairing code
            browser: ["Ubuntu", "Chrome", "110.0.5481.177"]
        }});

        // Aceasta este funcția care FORȚEAZĂ codul de 8 cifre
        if (!sock.authState.creds.registered) {{
            console.log('BOT:GENERATING_CODE');
            try {{
                await delay(5000); // Așteptăm să se inițializeze socket-ul
                const code = await sock.requestPairingCode('{MY_PHONE}');
                console.log('PAIRING_CODE:' + code);
            }} catch (err) {{
                console.log('BOT:ERROR:' + err.message);
            }}
        }}

        sock.ev.on('creds.update', saveCreds);
        sock.ev.on('connection.update', (update) => {{
            const {{ connection, qr }} = update;
            if (qr) console.log('BOT:STILL_QR_DETECTED'); // Nu ar trebui să apară
            if (connection === 'open') console.log('BOT:CONNECTED');
            if (connection === 'close') connect();
        }});
    }}
    connect();
    """
    
    with open("bridge.js", "w") as f:
        f.write(node_code)

    # Pornim Node.js și urmărim output-ul în loguri
    process = subprocess.Popen(["node", "bridge.js"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        clean_line = line.strip()
        print(f"DEBUG: {clean_line}") # Asta va apărea în logurile Railway
        
        if "PAIRING_CODE:" in clean_line:
            pairing_code = clean_line.split("PAIRING_CODE:")[1]
            bot_status = "Cod Generat!"
        elif "BOT:CONNECTED" in clean_line:
            bot_status = "CONECTAT"
            pairing_code = "CONECTAT"
        elif "BOT:ERROR" in clean_line:
            bot_status = "Eroare: " + clean_line

threading.Thread(target=run_wa_bridge, daemon=True).start()

@app.route('/login')
def login():
    return render_template_string('''
        <body style="text-align: center; font-family: sans-serif; padding-top: 50px; background: #f0f2f5;">
            <div style="background: white; display: inline-block; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <h1 style="color: #075E54;">WhatsApp AI Pairing</h1>
                <p>Status: <strong>{{status}}</strong></p>
                
                {% if code != "CONECTAT" and code != "Se generează..." %}
                    <div style="background: #e1ffeb; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <span style="font-size: 3.5em; letter-spacing: 8px; font-weight: bold; color: #128C7E;">{{code}}</span>
                    </div>
                    <div style="text-align: left; display: inline-block;">
                        <p>1. Deschide WhatsApp pe telefon</p>
                        <p>2. Mergi la <b>Dispozitive conectate</b></p>
                        <p>3. Apasă <b>Conectați un dispozitiv</b></p>
                        <p>4. Apasă jos pe <b>"Conectați folosind numărul de telefon"</b></p>
                        <p>5. Introdu codul de mai sus</p>
                    </div>
                {% elif code == "Se generează..." %}
                    <p>Se generează codul pentru {{phone}}... te rugăm așteaptă 10 secunde.</p>
                {% else %}
                    <h2 style="color: #25D366;">✅ Conexiune Reușită!</h2>
                    <p>Poți închide această pagină.</p>
                {% endif %}
            </div>
            <script>setTimeout(() => location.reload(), 8000);</script>
        </body>
    ''', status=bot_status, code=pairing_code, phone=MY_PHONE)

@app.route('/')
def health(): return "Serverul OpenClaw este activ!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

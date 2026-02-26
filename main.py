import os
import subprocess
import threading
import json
import base64
from io import BytesIO
import qrcode
from flask import Flask, render_template_string, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURARE AI ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- CONFIGURARE BOT ---
MY_PHONE = "40753873825"  # <--- PUNE NUMĂRUL TĂU AICI (format 407...)
pairing_code = "Se generează..."
bot_status = "Inițializare..."
wa_process = None

def run_wa_bridge():
    global pairing_code, bot_status, wa_process
    
    node_code = f"""
    const {{ default: makeWASocket, useMultiFileAuthState, delay, fetchLatestBaileysVersion, DisconnectReason }} = require('@whiskeysockets/baileys');
    const pino = require('pino');

    async function connect() {{
        const {{ state, saveCreds }} = await useMultiFileAuthState('auth_session_final');
        const {{ version }} = await fetchLatestBaileysVersion();

        const sock = makeWASocket({{
            version,
            auth: state,
            printQRInTerminal: false,
            logger: pino({{ level: 'silent' }}),
            browser: ["Ubuntu", "Chrome", "110.0.5481.177"]
        }});

        if (!sock.authState.creds.registered) {{
            await delay(5000);
            const code = await sock.requestPairingCode('{MY_PHONE}');
            console.log('PAIRING_CODE:' + code);
        }}

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', (update) => {{
            const {{ connection, lastDisconnect }} = update;
            if (connection === 'open') console.log('BOT_STATUS:CONNECTED');
            if (connection === 'close') {{
                const shouldReconnect = lastDisconnect.error?.output?.statusCode !== DisconnectReason.loggedOut;
                if (shouldReconnect) connect();
            }}
        }});

        sock.ev.on('messages.upsert', async m => {{
            const msg = m.messages[0];
            if (!msg.key.fromMe && msg.message) {{
                const from = msg.key.remoteJid;
                const text = msg.message.conversation || msg.message.extendedTextMessage?.text;
                if (text) {{
                    console.log('MSG_IN:' + from + '|' + text);
                }}
            }}
        }});

        // Ascultă comenzi de la Python (stdin)
        process.stdin.on('data', async (data) => {{
            try {{
                const cmd = JSON.parse(data.toString());
                if (cmd.action === 'send') {{
                    await sock.sendMessage(cmd.to, {{ text: cmd.text }});
                }}
            }} catch (e) {{}}
        }});
    }}
    connect();
    """
    
    with open("bridge.js", "w") as f:
        f.write(node_code)

    wa_process = subprocess.Popen(
        ["node", "bridge.js"], 
        stdout=subprocess.PIPE, 
        stdin=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        bufsize=1
    )

    for line in wa_process.stdout:
        line = line.strip()
        print(f"LOG: {line}") # Debug în Railway Logs

        if "PAIRING_CODE:" in line:
            pairing_code = line.split("PAIRING_CODE:")[1]
            bot_status = "Așteptare Pairing..."
        
        elif "BOT_STATUS:CONNECTED" in line:
            bot_status = "CONECTAT"
            pairing_code = "CONECTAT"

        elif "MSG_IN:" in line:
            try:
                # Format: MSG_IN:jid|text
                data_part = line.replace("MSG_IN:", "")
                jid, user_msg = data_part.split('|', 1)
                
                # Generare răspuns cu Gemini
                response = model.generate_content(f"Răspunde scurt și prietenos în română: {user_msg}")
                ai_text = response.text

                # Trimitere înapoi la WhatsApp prin stdin-ul procesului Node
                reply_cmd = json.dumps({"action": "send", "to": jid, "text": ai_text})
                wa_process.stdin.write(reply_cmd + "\n")
                wa_process.stdin.flush()
            except Exception as e:
                print(f"Eroare procesare mesaj: {e}")

# --- FLASK DASHBOARD ---

@app.route('/')
@app.route('/login')
def dashboard():
    return render_template_string('''
        <body style="text-align: center; font-family: sans-serif; padding-top: 50px; background: #f0f2f5;">
            <div style="background: white; display: inline-block; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <h1 style="color: #075E54;">WhatsApp Gemini AI</h1>
                <p>Status: <strong style="color: {{ 'green' if status == 'CONECTAT' else 'orange' }};">{{status}}</strong></p>
                
                {% if status != "CONECTAT" %}
                    <div style="background: #e1ffeb; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <span style="font-size: 3em; letter-spacing: 5px; font-weight: bold; color: #128C7E;">{{code}}</span>
                    </div>
                    <p>Introdu codul în WhatsApp -> Dispozitive Conectate -> Link with Phone Number</p>
                {% else %}
                    <div style="color: green; font-size: 1.2em;">🚀 Bot-ul este activ și răspunde la mesaje!</div>
                {% endif %}
            </div>
            <script>setTimeout(() => location.reload(), 10000);</script>
        </body>
    ''', status=bot_status, code=pairing_code)

if __name__ == "__main__":
    threading.Thread(target=run_wa_bridge, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

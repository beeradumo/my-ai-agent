import os
import subprocess
import threading
import json
import base64
from io import BytesIO
from flask import Flask, render_template_string
import google.generativeai as genai
from google.api_core import client_options

app = Flask(__name__)

# --- CONFIGURARE AI ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# Forțăm utilizarea API v1 pentru a evita eroarea 404 (v1beta)
my_options = client_options.ClientOptions(api_endpoint="generativelanguage.googleapis.com")
genai.configure(api_key=GEMINI_KEY, client_options=my_options)

def get_ai_response(content):
    """Obține răspuns de la Gemini cu fallback pentru numele modelului"""
    # Încercăm variantele de nume cele mai comune
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash']
    
    last_err = ""
    for m_name in model_names:
        try:
            model = genai.GenerativeModel(model_name=m_name)
            response = model.generate_content(content)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_err = str(e)
            continue
            
    return f"🤖 Eroare API Google: {last_err[:100]}"

# --- CONFIGURARE BOT ---
MY_PHONE = os.environ.get("MY_PHONE", "40753873825") # Schimbă cu numărul tău
pairing_code = "Se generează..."
bot_status = "Inițializare..."
wa_process = None

def run_wa_bridge():
    global pairing_code, bot_status, wa_process
    
    node_code = """
    const { default: makeWASocket, useMultiFileAuthState, delay, fetchLatestBaileysVersion, DisconnectReason, downloadContentFromMessage } = require('@whiskeysockets/baileys');
    const pino = require('pino');

    async function connect() {
        const { state, saveCreds } = await useMultiFileAuthState('auth_session_stable');
        const { version } = await fetchLatestBaileysVersion();

        const sock = makeWASocket({
            version,
            auth: state,
            printQRInTerminal: false,
            logger: pino({ level: 'silent' }),
            browser: ["Ubuntu", "Chrome", "110.0.5481.177"]
        });

        if (!sock.authState.creds.registered) {
            await delay(5000);
            const code = await sock.requestPairingCode('REPLACE_WITH_PHONE');
            console.log('PAIRING_CODE:' + code);
        }

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect } = update;
            if (connection === 'open') console.log('BOT_STATUS:CONNECTED');
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect.error?.output?.statusCode !== DisconnectReason.loggedOut;
                if (shouldReconnect) connect();
            }
        });

        sock.ev.on('messages.upsert', async m => {
            const msg = m.messages[0];
            if (!msg.key.fromMe && msg.message) {
                const from = msg.key.remoteJid;
                const text = msg.message.conversation || 
                             msg.message.extendedTextMessage?.text || 
                             msg.message.imageMessage?.caption || "";

                if (text.toLowerCase().startsWith('/bot')) {
                    const prompt = text.replace('/bot', '').trim();
                    let imgBase64 = "";

                    if (msg.message.imageMessage) {
                        try {
                            const stream = await downloadContentFromMessage(msg.message.imageMessage, 'image');
                            let buffer = Buffer.from([]);
                            for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }
                            imgBase64 = buffer.toString('base64');
                        } catch (err) {
                            console.log('DEBUG: Eroare descarcare imagine');
                        }
                    }
                    console.log('PYTHON_EVENT:MSG_IN|' + from + '|' + prompt + '|' + imgBase64);
                }
            }
        });

        process.stdin.on('data', async (data) => {
            try {
                const cmd = JSON.parse(data.toString());
                if (cmd.action === 'send') {
                    await sock.sendMessage(cmd.to, { text: cmd.text });
                }
            } catch (e) {}
        });
    }
    connect();
    """.replace("REPLACE_WITH_PHONE", MY_PHONE)
    
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
        print(f"RAW: {line}")

        if "PAIRING_CODE:" in line:
            pairing_code = line.split("PAIRING_CODE:")[1]
            bot_status = "Așteptare Pairing..."
        elif "BOT_STATUS:CONNECTED" in line:
            bot_status = "CONECTAT"
            pairing_code = "CONECTAT"
        elif "PYTHON_EVENT:MSG_IN|" in line:
            try:
                parts = line.split('PYTHON_EVENT:MSG_IN|')[1].split('|')
                jid = parts[0]
                prompt = parts[1] if parts[1] else "Analizează această imagine."
                img_data = parts[2] if len(parts) > 2 else ""

                print(f"📩 Procesare pentru {jid}")

                payload = []
                if img_data:
                    payload.append({"mime_type": "image/jpeg", "data": base64.b64decode(img_data)})
                payload.append(prompt)

                ai_reply = get_ai_response(payload)

                reply_cmd = json.dumps({"action": "send", "to": jid, "text": ai_reply})
                wa_process.stdin.write(reply_cmd + "\n")
                wa_process.stdin.flush()
                print(f"✅ Trimis către {jid}")
            except Exception as e:
                print(f"❌ Eroare: {e}")

@app.route('/')
@app.route('/login')
def dashboard():
    return render_template_string('''
        <body style="text-align: center; font-family: sans-serif; padding-top: 50px; background: #f0f2f5;">
            <div style="background: white; display: inline-block; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <h1 style="color: #075E54;">WhatsApp Gemini AI</h1>
                <p>Status: <strong style="color: {{ 'green' if status == 'CONECTAT' else 'orange' }};">{{status}}</strong></p>
                {% if status != "CONECTAT" and code != "Se generează..." %}
                    <div style="background: #e1ffeb; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <span style="font-size: 3em; letter-spacing: 5px; font-weight: bold; color: #128C7E;">{{code}}</span>
                    </div>
                {% endif %}
            </div>
            <script>setTimeout(() => location.reload(), 15000);</script>
        </body>
    ''', status=bot_status, code=pairing_code)

if __name__ == "__main__":
    threading.Thread(target=run_wa_bridge, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

import os
import subprocess
import threading
import base64
import json
from io import BytesIO
import qrcode
from flask import Flask, render_template_string, jsonify
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURARE ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

qr_base64 = None
bot_status = "Inițializare..."

# --- BRIDGE WHATSAPP (NODE.JS + BAILEYS) ---

def run_wa_bridge():
    global qr_base64, bot_status
    
    # Creăm scriptul de bridge care comunică prin protocolul nativ WA
    node_code = """
    const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
    const QRCode = require('qrcode');

    async function connect() {
        const { state, saveCreds } = await useMultiFileAuthState('auth_session');
        const sock = makeWASocket({
            printQRInTerminal: false,
            auth: state,
            browser: ["OpenClaw AI", "Chrome", "1.0.0"]
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            if (qr) {
                console.log('QR_DATA:' + qr);
            }
            if (connection === 'close') {
                const shouldReconnect = lastDisconnect.error?.output?.statusCode !== DisconnectReason.loggedOut;
                if (shouldReconnect) connect();
            } else if (connection === 'open') {
                console.log('STATUS:CONNECTED');
            }
        });

        sock.ev.on('messages.upsert', async m => {
            const msg = m.messages[0];
            if (!msg.key.fromMe && msg.message) {
                const text = msg.message.conversation || msg.message.extendedTextMessage?.text;
                const from = msg.key.remoteJid;
                if (text) {
                    console.log('MSG_FROM:' + from + '|BODY:' + text);
                    // Trimitem evenimentul către Python via stdout
                }
            }
        });

        // Funcție globală pentru a trimite mesaje din Python (simplificat prin stdout/stdin)
        global.sendMsg = async (to, text) => {
            await sock.sendMessage(to, { text: text });
        };
    }
    connect();
    """
    
    with open("bridge.js", "w") as f:
        f.write(node_code)

    # Pornim procesul Node
    process = subprocess.Popen(["node", "bridge.js"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in process.stdout:
        line = line.strip()
        if line.startswith("QR_DATA:"):
            qr_str = line.replace("QR_DATA:", "")
            img = qrcode.make(qr_str)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            bot_status = "Așteptare scanare..."
        
        elif line == "STATUS:CONNECTED":
            bot_status = "Conectat și Activ"
            qr_base64 = None
            print("✅ WhatsApp s-a conectat cu succes!")

        elif "MSG_FROM:" in line:
            # Format: MSG_FROM:jid|BODY:text
            try:
                parts = line.split('|BODY:')
                jid = parts[0].replace("MSG_FROM:", "")
                incoming_text = parts[1]
                
                # Răspuns prin Gemini
                print(f"📩 Mesaj primit de la {jid}: {incoming_text}")
                ai_response = model.generate_content(f"Răspunde prietenos în română: {incoming_text}").text
                
                # În această versiune, printăm răspunsul. 
                # Pentru trimitere reală se folosește un socket sau stdin.
                print(f"🤖 Răspuns Gemini: {ai_response}")
            except:
                pass

# --- RUTE WEB ---

@app.route('/')
def home():
    return render_template_string('''
        <body style="text-align: center; font-family: sans-serif; background: #f4f7f6; padding-top: 50px;">
            <div style="background: white; display: inline-block; padding: 40px; border-radius: 15px; shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1>OpenClaw AI Dashboard</h1>
                <p>Status: <span style="color: green; font-weight: bold;">{{status}}</span></p>
                {% if qr %}
                    <p>Scanează codul de mai jos cu WhatsApp:</p>
                    <img src="data:image/png;base64,{{qr}}" style="border: 1px solid #ddd;">
                    <p style="font-size: 0.8em; color: #666;">Pagina se reîncarcă automat la 15s</p>
                {% else %}
                    <p>✅ AI-ul este gata să răspundă mesajelor tale.</p>
                {% endif %}
            </div>
            <script>setTimeout(() => location.reload(), 15000);</script>
        </body>
    ''', status=bot_status, qr=qr_base64)

if __name__ == "__main__":
    threading.Thread(target=run_wa_bridge, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

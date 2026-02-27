import os, subprocess, threading, json, base64
from flask import Flask, render_template_string
import google.generativeai as genai
from google.api_core import client_options

app = Flask(__name__)

# --- CONFIG AI ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
my_options = client_options.ClientOptions(api_endpoint="generativelanguage.googleapis.com")
genai.configure(api_key=GEMINI_KEY, client_options=my_options)

def get_ai_response(content):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(content)
        return response.text.strip() if response.text else "🤖 Fără răspuns."
    except Exception as e:
        return f"🤖 Eroare: {str(e)[:50]}"

# --- CONFIG BOT ---
MY_PHONE = "40753873825" # PUNE NUMĂRUL TĂU AICI
pairing_code = "Se generează..."
bot_status = "Inițializare..."
wa_process = None

def run_wa_bridge():
    global pairing_code, bot_status, wa_process
    
    # Am schimbat folderul de sesiune în 'session_reset_now' pentru a forța un cod nou
    node_code = """
    const { default: makeWASocket, useMultiFileAuthState, delay, fetchLatestBaileysVersion, DisconnectReason, downloadContentFromMessage } = require('@whiskeysockets/baileys');
    const pino = require('pino');

    async function connect() {
        const { state, saveCreds } = await useMultiFileAuthState('session_reset_now'); 
        const { version } = await fetchLatestBaileysVersion();

        const sock = makeWASocket({
            version,
            auth: state,
            printQRInTerminal: false,
            logger: pino({ level: 'silent' }),
            browser: ["Ubuntu", "Chrome", "110.0.5481.177"]
        });

        if (!sock.authState.creds.registered) {
            await delay(3000);
            const code = await sock.requestPairingCode('REPLACE_WITH_PHONE');
            console.log('PAIRING_CODE:' + code);
        }

        sock.ev.on('creds.update', saveCreds);
        sock.ev.on('connection.update', (u) => {
            if (u.connection === 'open') console.log('BOT_STATUS:CONNECTED');
            if (u.connection === 'close') connect();
        });

        sock.ev.on('messages.upsert', async m => {
            const msg = m.messages[0];
            if (!msg.key.fromMe && msg.message) {
                const from = msg.key.remoteJid;
                const text = msg.message.conversation || msg.message.extendedTextMessage?.text || msg.message.imageMessage?.caption || "";
                if (text.toLowerCase().startsWith('/bot')) {
                    const prompt = text.replace('/bot', '').trim();
                    let imgBase64 = "";
                    if (msg.message.imageMessage) {
                        const stream = await downloadContentFromMessage(msg.message.imageMessage, 'image');
                        let buffer = Buffer.from([]);
                        for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }
                        imgBase64 = buffer.toString('base64');
                    }
                    console.log('PYTHON_EVENT:MSG_IN|' + from + '|' + prompt + '|' + imgBase64);
                }
            }
        });

        process.stdin.on('data', async (d) => {
            try {
                const cmd = JSON.parse(d.toString());
                if (cmd.action === 'send') await sock.sendMessage(cmd.to, { text: cmd.text });
            } catch (e) {}
        });
    }
    connect();
    """.replace("REPLACE_WITH_PHONE", MY_PHONE)
    
    with open("bridge.js", "w") as f: f.write(node_code)

    wa_process = subprocess.Popen(["node", "bridge.js"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

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
                jid, prompt, img = parts[0], parts[1], parts[2]
                payload = []
                if img: payload.append({"mime_type": "image/jpeg", "data": base64.b64decode(img)})
                payload.append(prompt if prompt else "Analizează imaginea.")
                reply = get_ai_response(payload)
                wa_process.stdin.write(json.dumps({"action": "send", "to": jid, "text": reply}) + "\\n")
                wa_process.stdin.flush()
            except: pass

@app.route('/')
def dash():
    return render_template_string('<h1>Status: {{s}}</h1><h2>Cod: {{c}}</h2>', s=bot_status, c=pairing_code)

if __name__ == "__main__":
    threading.Thread(target=run_wa_bridge, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

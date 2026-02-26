import os
import asyncio
import threading
import base64
from io import BytesIO
from flask import Flask, send_file, render_template_string, jsonify
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURARE ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Stocăm starea QR-ului global
qr_image_base64 = None
whatsapp_status = "Inițializare..."

# --- LOGICA WHATSAPP (BROWSER) ---

async def run_whatsapp():
    global qr_image_base64, whatsapp_status
    
    async with async_playwright() as p:
        # Lansăm browserul cu setări de economisire memorie pentru Railway
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage', 
                '--disable-gpu'
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)
        
        print("🌐 Navigăm către WhatsApp Web...")
        await page.goto("https://web.whatsapp.com")
        whatsapp_status = "Așteptare Cod QR..."

        while True:
            try:
                # 1. Verificăm dacă suntem deja logați
                if await page.query_selector("text=Search"):
                    whatsapp_status = "Conectat"
                    qr_image_base64 = None
                    
                    # Logica de ascultare mesaje (simplificată)
                    # Aici se poate extinde pentru a citi DOM-ul
                    await asyncio.sleep(30)
                    continue

                # 2. Încercăm să capturăm codul QR dacă apare
                qr_canvas = await page.wait_for_selector("canvas", timeout=10000)
                if qr_canvas:
                    # Facem un screenshot doar la elementul Canvas (codul QR)
                    img_bytes = await qr_canvas.screenshot()
                    qr_image_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    whatsapp_status = "Cod QR disponibil pentru scanare"
            
            except Exception as e:
                print(f"Sistem: {e}")
            
            await asyncio.sleep(5)

# Thread separat pentru a nu bloca Flask
def start_browser_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_whatsapp())

# --- RUTE FLASK ---

@app.route('/')
def index():
    return jsonify({
        "status": whatsapp_status,
        "api": "Gemini 1.5 Flash",
        "system": "Active"
    })

@app.route('/login')
def login():
    if whatsapp_status == "Conectat":
        return "<h1>WhatsApp este deja CONECTAT!</h1><a href='/'>Înapoi</a>"
    
    return render_template_string('''
        <html>
            <head>
                <title>OpenClaw WA Login</title>
                <meta http-equiv="refresh" content="10">
                <style>
                    body { font-family: Arial; text-align: center; background: #f0f2f5; padding-top: 50px; }
                    .card { background: white; display: inline-block; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
                    img { border: 1px solid #ddd; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>Scanează pentru Conectare AI</h2>
                    <p>Status: <strong>{{status}}</strong></p>
                    {% if qr %}
                        <img src="data:image/png;base64,{{qr}}" width="264">
                    {% else %}
                        <p>Se încarcă codul QR... te rugăm așteaptă.</p>
                    {% endif %}
                    <p>Deschide WhatsApp pe telefon -> Dispozitive conectate</p>
                </div>
            </body>
        </html>
    ''', qr=qr_image_base64, status=whatsapp_status)

if __name__ == "__main__":
    # Pornim motorul de browser
    threading.Thread(target=start_browser_loop, daemon=True).start()
    
    # Pornim serverul web
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

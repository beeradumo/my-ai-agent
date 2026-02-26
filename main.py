import os
from openclaw import Agent
from openclaw.tools import GmailTool, WhatsAppTool # Presupunem că folosim conectorii lor
import google.generativeai as genai

# 1. Configurăm "Creierul" (Gemini)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 2. Definim instrucțiunile asistentului (Personalitatea)
SYSTEM_PROMPT = """
Ești un asistent personal inteligent numit 'Claw-AI'. 
Misiunea ta: ajută utilizatorul cu Gmail și WhatsApp.
Dacă utilizatorul cere să trimită un mail, folosește GmailTool.
Dacă întreabă de mesaje noi, verifică ambele platforme.
Răspunde mereu politicos și concis în limba Română.
"""

# 3. Inițializăm Agentul OpenClaw
agent = Agent(
    name="Claw-AI",
    description="Asistent pentru productivitate",
    instructions=SYSTEM_PROMPT,
    tools=[GmailTool(), WhatsAppTool()] # Aici adăugăm uneltele pe care le vom configura
)

# 4. Funcția principală de procesare (Logica)
def proceseaza_cerere(mesaj_utilizator):
    # Trimitem mesajul către Gemini pentru a decide ce să facă
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Aici OpenClaw preia controlul și decide dacă trebuie să apeleze o funcție (Tool)
    raspuns = agent.run(mesaj_utilizator) 
    return raspuns

if __name__ == "__main__":
    # Pornim un mic server web pentru a primi mesaje (Webhook)
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route("/ask", methods=["POST"])
    def ask():
        user_input = request.json.get("text")
        result = proceseaza_cerere(user_input)
        return jsonify({"reply": result})

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

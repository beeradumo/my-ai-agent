FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

WORKDIR /app

# Instalăm dependențele de sistem (Am adăugat GIT)
RUN apt-get update && apt-get install -y \
    libvips-dev \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Instalăm motorul de WhatsApp (Baileys)
# Folosim --no-audit pentru viteză pe Railway
RUN npm install @whiskeysockets/baileys qrcode terminal-kit pino

# Instalăm dependențele Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem restul fișierelor
COPY . .

# Expunem portul pentru Railway
ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]

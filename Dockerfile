FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

WORKDIR /app

# Instalăm dependențele de sistem necesare
RUN apt-get update && apt-get install -y \
    libvips-dev \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Instalăm motorul de WhatsApp (Baileys) și utilitarele Node
RUN npm install @whiskeysockets/baileys qrcode pino

# Instalăm dependențele Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem codul sursă
COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]

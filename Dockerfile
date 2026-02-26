# Folosim Python 3.10 sau 3.11 pentru stabilitate cu AI
FROM python:3.11-slim

# Instalăm dependențele de sistem necesare pentru scriptul de install și OpenClaw
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Executăm instalarea oficială OpenClaw pentru Linux
RUN curl -fsSL https://openclaw.ai/install.sh | bash

# Adăugăm folderul OpenClaw în PATH-ul sistemului (foarte important pentru importuri)
# De obicei se instalează în ~/.openclaw sau /usr/local/bin
ENV PATH="/root/.openclaw/bin:/usr/local/bin:${PATH}"

# Copiem restul fișierelor (inclusiv requirements.txt și main.py)
COPY . .

# Instalăm dependințele Python (Gemini, Flask, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Pornim aplicația
CMD ["python", "main.py"]

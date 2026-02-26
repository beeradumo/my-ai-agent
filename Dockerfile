# Folosim o imagine Python stabilă
FROM python:3.11-slim

# Pasul critic: Instalăm curl și packetele de sistem necesare
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Rulăm scriptul de instalare OpenClaw
# Folosim bash explicit și verificăm unde se instalează
RUN curl -fsSL https://openclaw.ai/install.sh | bash

# Adăugăm binarele OpenClaw în PATH (Railway are nevoie de asta pentru a vedea 'openclaw')
ENV PATH="/root/.openclaw/bin:/usr/local/bin:${PATH}"

# Copiem fișierele tale (main.py, requirements.txt)
COPY . .

# Instalăm restul librăriilor (Gemini, Flask, etc.)
# ASIGURĂ-TE că ai eliminat 'openclaw' din requirements.txt 
# pentru a evita conflictul cu ce am instalat mai sus prin script
RUN pip install --no-cache-dir -r requirements.txt

# Pornim aplicația
CMD ["python", "main.py"]

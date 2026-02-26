FROM python:3.11-slim

# Instalăm dependențele minime. Am scos 'sudo' ca să evităm erorile de permisiuni.
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Metoda alternativă: Descărcăm scriptul, dar îl "curățăm" de sudo înainte de rulare
RUN curl -fsSL https://openclaw.ai/install.sh -o install.sh && \
    sed -i 's/sudo //g' install.sh && \
    sh install.sh

# Forțăm instalarea librăriei de bază dacă scriptul a eșuat silențios
# Dacă 'openclaw' nu e în pip, îl instalăm ca modul local din ce a descărcat scriptul
ENV PYTHONPATH="${PYTHONPATH}:/root/.openclaw/lib"
ENV PATH="/root/.openclaw/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

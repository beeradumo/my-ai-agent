FROM python:3.11-slim

# Instalăm dependențele minime de sistem
RUN apt-get update && apt-get install -y \
    curl git gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# În loc de scriptul .sh, instalăm framework-ul direct de pe repository-ul lor
# Notă: Aceasta este metoda recomandată pentru deployment-uri de server
RUN pip install --no-cache-dir git+https://github.com/openclaw/openclaw-python.git

# Copiem restul dependențelor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem codul sursă
COPY . .

# Setăm variabila de mediu pentru a vedea logurile în timp real
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]

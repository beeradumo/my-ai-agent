import os
import openclaw
import sys

print("--- DEBUG OPENCLAW ---")
print(f"Locație pachet: {openclaw.__file__}")
print(f"Versiune Python: {sys.version}")
print(f"Ce conține pachetul: {dir(openclaw)}")

# Încercăm să vedem dacă Agent este ascuns sub alt nume sau submodul
try:
    from openclaw.agents import Agent
    print("✅ Gasit sub: openclaw.agents")
except ImportError:
    try:
        from openclaw.core import Agent
        print("✅ Gasit sub: openclaw.core")
    except ImportError:
        print("❌ Agent nu a fost găsit în submodelele standard.")

# Dacă scriptul de install.sh a pus ceva în /usr/local/bin, verificăm și acolo
print("--- VERIFICARE SISTEM ---")
os.system("ls -la /usr/local/bin/openclaw*")
os.system("openclaw --version")

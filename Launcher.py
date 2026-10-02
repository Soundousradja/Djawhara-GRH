import os
import sys
import threading
import time
import socket

import django
import webview
from django.core.management import call_command


# ============================================================
# Déterminer le dossier de l'application
# ============================================================

if getattr(sys, "frozen", False):
    # Application compilée avec PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Application en développement
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

# Indiquer à Django où se trouvent les settings
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "djawhara_grh.settings"
)

django.setup()


# ============================================================
# Démarrer Django
# ============================================================

def start_django():
    try:
        call_command(
            "runserver",
            "127.0.0.1:8000",
            use_reloader=False
        )
    except Exception as e:
        print("Erreur Django :", e)


django_thread = threading.Thread(
    target=start_django,
    daemon=True
)

django_thread.start()


# ============================================================
# Attendre que Django soit prêt
# ============================================================

for _ in range(30):
    try:
        with socket.create_connection(
            ("127.0.0.1", 8000),
            timeout=1
        ):
            break
    except OSError:
        time.sleep(1)
else:
    raise RuntimeError(
        "Impossible de démarrer le serveur Django."
    )


# ============================================================
# Ouvrir l'application dans une fenêtre
# ============================================================

webview.create_window(
    "Djawhara GRH",
    "http://127.0.0.1:8000",
    width=1200,
    height=800,
    resizable=True
)

webview.start()
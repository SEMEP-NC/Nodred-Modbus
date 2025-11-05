from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
import logging
import json
import os
import signal
import sys
import threading
import time

# === Configuration logging ===
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# === Configuration ===
STATE_FILE = os.getenv("MODBUS_STATE_FILE", "/data/modbus_state.json")
SAVE_INTERVAL_SECONDS = 30  # 30 secondes
REGISTER_COUNT = 1000       # <=== NOUVELLE TAILLE

save_lock = threading.Lock()

# === Fonctions de sauvegarde/restauration ===

def save_registers(context):
    """Sauvegarde l'état actuel des registres dans un fichier JSON."""
    try:
        with save_lock:
            hr = context[0].getValues(3, 0, count=REGISTER_COUNT)  # Holding Registers
            co = context[0].getValues(1, 0, count=REGISTER_COUNT)  # Coils

            state = {"hr": hr, "co": co}

            with open(STATE_FILE, "w") as f:
                json.dump(state, f)

        log.info("💾 Sauvegarde automatique effectuée (%d registres).", REGISTER_COUNT)
    except Exception as e:
        log.error("Erreur lors de la sauvegarde : %s", e)

def load_registers(context):
    """Recharge les registres à partir du fichier JSON s'il existe."""
    if os.path.exists(STATE_FILE):
        log.info("Chargement de l’état depuis %s...", STATE_FILE)
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            hr = state.get("hr", [0] * REGISTER_COUNT)
            co = state.get("co", [0] * REGISTER_COUNT)
            context[0].setValues(3, 0, hr)
            context[0].setValues(1, 0, co)
            log.info("✅ État restauré avec succès (%d registres).", REGISTER_COUNT)
        except Exception as e:
            log.error("Erreur lors de la restauration : %s", e)
    else:
        log.info("Aucun fichier de sauvegarde trouvé. Utilisation des valeurs par défaut (%d registres).", REGISTER_COUNT)
        context[0].setValues(3, 0, [0] * REGISTER_COUNT)
        context[0].setValues(1, 0, [0] * REGISTER_COUNT)

# === Thread de sauvegarde périodique ===

def periodic_saver(context):
    """Thread pour sauvegarder périodiquement l'état des registres."""
    while True:
        time.sleep(SAVE_INTERVAL_SECONDS)
        save_registers(context)

# === Définir les blocs de données ===

store = ModbusSlaveContext(
    co=ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT),
    hr=ModbusSequentialDataBlock(0, [0] * REGISTER_COUNT),
)

context = ModbusServerContext(slaves=store, single=True)

# === Charger les valeurs sauvegardées au besoin ===
load_registers(context)

# === Gérer l’arrêt propre ===

def handle_exit(signum, frame):
    log.info("⏹ Arrêt du serveur... sauvegarde en cours.")
    save_registers(context)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# === Lancement du thread de sauvegarde périodique ===
thread = threading.Thread(target=periodic_saver, args=(context,), daemon=True)
thread.start()

# === Informations du serveur ===
identity = ModbusDeviceIdentification()
identity.VendorName = "SEMEP"
identity.ProductCode = "PM"
identity.VendorUrl = "http://example.com"
identity.ProductName = "Modbus Server"
identity.ModelName = "Modbus TCP Server"
identity.MajorMinorRevision = "1.1"

# === Lancement du serveur Modbus TCP ===
log.info("🚀 Serveur Modbus TCP démarré sur 0.0.0.0:1502 avec %d registres.", REGISTER_COUNT)

StartTcpServer(
    context=context,
    identity=identity,
    address=("0.0.0.0", 1502)
)

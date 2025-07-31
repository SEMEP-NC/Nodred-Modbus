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

STATE_FILE = "modbus_state.json"
SAVE_INTERVAL_SECONDS = 300  # 5 minutes

# === Fonctions de sauvegarde/restauration ===

def save_registers(context):
    try:
        hr = context[0].getValues(3, 0, count=100)  # Holding Registers
        co = context[0].getValues(1, 0, count=100)  # Coils

        state = {
            "hr": hr,
            "co": co
        }

        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

        log.info("Sauvegarde automatique effectuée.")
    except Exception as e:
        log.warning("Échec de la sauvegarde : %s", e)


def load_registers(context):
    if os.path.exists(STATE_FILE):
        log.info("Chargement de l’état depuis %s...", STATE_FILE)
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            context[0].setValues(3, 0, state.get("hr", [0]*100))  # Holding Registers
            context[0].setValues(1, 0, state.get("co", [0]*100))  # Coils
            log.info("État restauré avec succès.")
        except Exception as e:
            log.warning("Erreur de restauration : %s", e)
    else:
        log.info("Aucun fichier de sauvegarde trouvé. Utilisation des valeurs par défaut.")


# === Thread de sauvegarde périodique ===

def periodic_saver(context):
    while True:
        time.sleep(SAVE_INTERVAL_SECONDS)
        save_registers(context)


# === Définir les blocs de données ===

store = ModbusSlaveContext(
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
)

context = ModbusServerContext(slaves=store, single=True)

# === Charger les valeurs sauvegardées au besoin ===
load_registers(context)

# === Gérer l’arrêt propre ===

def handle_exit(signum, frame):
    log.info("Arrêt du serveur... sauvegarde en cours.")
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
identity.MajorMinorRevision = "1.0"

# === Lancement du serveur ===
log.info("Serveur Modbus TCP démarré sur 0.0.0.0:1502")
StartTcpServer(context, identity=identity, address=("0.0.0.0", 1502))

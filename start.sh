#!/bin/bash

set -e

echo "----------------------------------------"
echo "[+] Initialisation du conteneur Node-RED + Modbus"
echo "----------------------------------------"

# Démarrer Node-RED avec le répertoire de données spécifié
echo "[+] Démarrage de Node-RED..."
node-red -u /data &

# Enregistrer le PID de Node-RED
NODE_RED_PID=$!

# Optionnel : pause pour laisser Node-RED démarrer correctement
sleep 2

# Démarrer le serveur Python Modbus
echo "[+] Démarrage du serveur Python Modbus..."
if [ -f "/app/modbus_server.py" ]; then
    python3 /app/modbus_server.py &
    MODBUS_PID=$!
else
    echo "[!] ERREUR : /app/modbus_server.py introuvable. Le serveur Python ne sera pas lancé."
    MODBUS_PID=""
fi

echo "----------------------------------------"
echo "[✓] Services lancés. En attente..."
echo "----------------------------------------"

# Attente des processus enfants
if [ -n "$MODBUS_PID" ]; then
    wait $NODE_RED_PID $MODBUS_PID
else
    wait $NODE_RED_PID
fi



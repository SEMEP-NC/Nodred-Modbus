FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_RED_HOME=/data
ENV MODBUS_STATE_FILE=/data/modbus_state.json

# --- Mises à jour système + dépendances
RUN apt-get update && apt-get install -y \
    curl python3 python3-pip git build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Installer Node-RED + plugins
RUN npm install -g --unsafe-perm node-red \
    node-red-contrib-modbus \
    node-red-contrib-knx-ultimate

# --- Définir le dossier de travail
WORKDIR /app

# --- Installer les dépendances Python
COPY requirements.txt ./requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# --- Copier le projet
COPY . .

# --- Assurer que le script de démarrage est exécutable
RUN chmod +x /app/start.sh

# --- Préparer le dossier /data (pour persistance)
RUN mkdir -p /data
COPY flows.json /data/flows.json

# --- Exposer les ports nécessaires
EXPOSE 1880 1502

# --- Healthcheck optionnel
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:1880 || exit 1

# --- Point d'entrée : démarrage du script
CMD ["bash", "/app/start.sh"]

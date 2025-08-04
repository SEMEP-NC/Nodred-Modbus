FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_RED_HOME=/data

# --- Mises à jour système + dépendances
RUN apt-get update && apt-get install -y \
    curl python3 python3-pip git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

# --- Installer Node-RED + plugins
RUN npm install -g --unsafe-perm node-red \
    node-red-contrib-modbus \
    node-red-contrib-knx-ultimate

# --- Installer dépendances Python
COPY requirements.txt /app/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /app/requirements.txt

# --- Structure du projet
WORKDIR /app
COPY . /app
RUN chmod +x /app/start.sh

# --- Préparer le dossier de flow Node-RED
RUN mkdir -p /data
COPY flows.json /data/flows.json

# --- Ports exposés
EXPOSE 1880 502 1502

# --- Lancer l’environnement
CMD ["bash", "/app/start.sh"]


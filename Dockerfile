# Multi-stage Dockerfile pour Visibility Tracker
# Optimisé pour un déploiement sur VPS avec base path /nom-outil/

# ================================
# Stage 1: Build Frontend
# ================================
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copier les fichiers de configuration
COPY frontend/package*.json ./
COPY frontend/yarn.lock* ./

# Installer les dépendances
RUN npm ci --only=production

# Copier le code source frontend
COPY frontend/ ./

# Build pour production avec base path
ENV NODE_ENV=production
RUN npm run build

# ================================
# Stage 2: Build Backend
# ================================
FROM python:3.11-slim as backend-builder

WORKDIR /app/backend

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY backend/requirements.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# Stage 3: Production Runtime
# ================================
FROM python:3.11-slim

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Installer les dépendances système pour l'exécution
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copier l'application backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/
COPY backend/ ./backend/

# Copier les fichiers buildés du frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Configuration Nginx pour servir le frontend et proxy l'API
RUN rm /etc/nginx/sites-enabled/default
COPY <<'EOF' /etc/nginx/sites-available/visibility-tracker
server {
    listen 80;
    server_name localhost;
    
    # Servir les fichiers statiques du frontend avec le base path
    location /nom-outil/ {
        alias /app/frontend/dist/;
        try_files $uri $uri/ /nom-outil/index.html;
        
        # Headers pour les assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy pour l'API backend avec le root path
    location /nom-outil/api/ {
        proxy_pass http://127.0.0.1:8021/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Support WebSocket si nécessaire
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /nom-outil/health {
        proxy_pass http://127.0.0.1:8021/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

RUN ln -s /etc/nginx/sites-available/visibility-tracker /etc/nginx/sites-enabled/

# Script de démarrage
COPY <<'EOF' /app/start.sh
#!/bin/bash
set -e

echo "🚀 Démarrage de Visibility Tracker..."

# Démarrer Nginx en arrière-plan
echo "📝 Démarrage de Nginx..."
nginx

# Démarrer l'API FastAPI avec le root path
echo "🔧 Démarrage de l'API Backend..."
cd /app/backend
export ROOT_PATH="/nom-outil"
exec python -m uvicorn main:app --host 127.0.0.1 --port 8021 --root-path /nom-outil
EOF

RUN chmod +x /app/start.sh

# Créer le dossier data et changer la propriété vers l'utilisateur app
RUN mkdir -p /app/backend/data && chown -R app:app /app
USER app

# Variables d'environnement pour la production
ENV PYTHONPATH="/app/backend"
ENV ROOT_PATH="/nom-outil"

# Exposition du port
EXPOSE 80

# Installer curl pour le health check
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/nom-outil/health || exit 1

# Point d'entrée
CMD ["/app/start.sh"]
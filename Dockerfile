# Multi-stage Dockerfile pour Visibility Tracker
# Optimisé pour un déploiement sur VPS avec Caddy comme reverse proxy

# ================================
# Stage 1: Build Frontend
# ================================
FROM node:18-alpine as frontend-builder

WORKDIR /app

# Copier les fichiers de configuration
COPY ./frontend/package*.json ./
COPY ./frontend/yarn.lock* ./

# Installer les dépendances
RUN npm ci

# Copier le code source frontend
COPY ./frontend/ ./

# Build pour production avec base path
ENV NODE_ENV=production
RUN npx vite build

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
COPY ./backend/requirements.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# Stage 3: Production Runtime
# ================================
FROM python:3.11-slim

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copier l'application backend
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/
COPY ./backend/ ./backend/

# Copier les fichiers buildés du frontend
COPY --from=frontend-builder /app/dist ./backend/static

# Créer le dossier data avec les bonnes permissions
RUN mkdir -p /app/backend/data && chown -R app:app /app

# Changer vers l'utilisateur app
USER app

# Variables d'environnement pour la production
ENV PYTHONPATH="/app/backend"
ENV ROOT_PATH="/visibility"

# Exposition du port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')"

# Point d'entrée  
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--root-path", "/visibility"]
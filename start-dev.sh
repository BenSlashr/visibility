#!/bin/bash

echo "🚀 Démarrage de Visibility Tracker en mode développement"

# Couleurs pour les logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour démarrer le backend
start_backend() {
    echo -e "${BLUE}📡 Démarrage du backend FastAPI...${NC}"
    cd backend
    
    # Créer le dossier data s'il n'existe pas
    mkdir -p data
    
    # Activer l'environnement virtuel s'il existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "⚠️  Environnement virtuel non trouvé. Créez-le avec:"
        echo "   cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
    
    # Démarrer FastAPI
    uvicorn main:app --reload --port 8021 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend démarré sur http://localhost:8021${NC}"
    cd ..
}

# Fonction pour démarrer le frontend
start_frontend() {
    echo -e "${BLUE}🎨 Démarrage du frontend React...${NC}"
    cd frontend
    
    # Installer les dépendances si node_modules n'existe pas
    if [ ! -d "node_modules" ]; then
        echo "📦 Installation des dépendances..."
        npm install
    fi
    
    # Démarrer Vite
    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend démarré sur http://localhost:3000${NC}"
    cd ..
}

# Démarrer les deux services
start_backend
sleep 2
start_frontend

echo ""
echo -e "${GREEN}🎉 Visibility Tracker est prêt !${NC}"
echo "   - Backend API: http://localhost:8021"
echo "   - Frontend: http://localhost:3000"
echo "   - API Docs: http://localhost:8021/docs"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter les services"

# Attendre et nettoyer à l'arrêt
trap 'echo "Arrêt des services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait 
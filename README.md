# Visibility Tracker

Application web pour analyser la visibilité des marques/sites dans les réponses des LLM (ChatGPT, Claude, etc.).

## 🎯 Concept

L'utilisateur crée des projets, définit des prompts d'analyse, exécute ces prompts via différentes IA, et obtient des métriques de visibilité.

## 🏗️ Architecture

- **Backend**: FastAPI (port 8021)
- **Frontend**: React + TypeScript + Vite (port 3000)  
- **Base de données**: SQLite locale (`data/visibility.db`)
- **Communication**: HTTP/JSON entre front et back

## 🚀 Installation

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8021
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📋 Fonctionnalités

1. **Gestion des projets** - Créer/modifier/supprimer des projets SEO
2. **Gestion des prompts** - Templates avec variables et modèles IA
3. **Exécution d'analyses** - Appels aux LLM et analyse des réponses
4. **Métriques et dashboard** - Suivi de la visibilité dans le temps

## 🔧 Développement

- Backend API docs: http://localhost:8021/docs
- Frontend dev server: http://localhost:3000 
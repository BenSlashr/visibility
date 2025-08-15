# Structure du projet Visibility Tracker

```
Visibility-V2/
├── README.md                    # Documentation principale
├── .gitignore                   # Fichiers à ignorer par Git
├── docker-compose.dev.yml       # ✅ Environnement de développement Docker
├── env.example                  # ✅ Variables d'environnement globales
├── start-dev.sh                 # Script de démarrage développement
├── STRUCTURE.md                 # Ce fichier
│
├── backend/                     # API FastAPI
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── requirements.txt         # Dépendances Python
│   ├── alembic.ini              # ✅ Configuration migrations
│   ├── env.example              # ✅ Variables backend
│   ├── alembic/                 # ✅ Migrations de base de données
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/                     # Package principal
│   │   ├── __init__.py
│   │   ├── core/                # ✅ Configuration + database
│   │   │   ├── config.py        # Settings centralisées
│   │   │   ├── database.py      # Configuration SQLAlchemy
│   │   │   └── deps.py          # Dépendances FastAPI
│   │   ├── models/              # Modèles SQLAlchemy
│   │   ├── schemas/             # ✅ Schémas Pydantic
│   │   ├── crud/                # ✅ Opérations base de données
│   │   ├── api/                 
│   │   │   └── v1/              # ✅ API versionnée
│   │   │       ├── endpoints/   # Routes spécialisées
│   │   │       └── router.py    # Routeur principal
│   │   ├── services/            # Logique métier
│   │   └── utils/               # ✅ Fonctions utilitaires
│   ├── tests/                   # ✅ Tests API
│   └── data/                    # Base de données (créé automatiquement)
│       └── visibility.db
│
└── frontend/                    # Application React
    ├── package.json             # Dépendances Node.js
    ├── vite.config.ts           # Configuration Vite
    ├── tsconfig.json            # Configuration TypeScript
    ├── tsconfig.node.json       # Config TS pour les outils
    ├── tailwind.config.js       # Configuration Tailwind CSS
    ├── postcss.config.js        # Configuration PostCSS
    ├── index.html               # Template HTML principal
    ├── env.example              # ✅ Variables frontend
    └── src/                     # Code source React
        ├── main.tsx             # Point d'entrée React
        ├── App.tsx              # Composant principal
        ├── index.css            # Styles globaux
        ├── components/          # ✅ Composants UI
        │   ├── ui/              # Composants de base
        │   │   └── Button.tsx
        │   ├── ProjectCard.tsx  # Composants métier
        │   └── PromptEditor.tsx
        ├── pages/               # ✅ Pages de l'application
        │   ├── ProjectsPage.tsx
        │   ├── PromptsPage.tsx
        │   └── DashboardPage.tsx
        ├── hooks/               # ✅ Hooks personnalisés
        │   └── useProjects.ts
        ├── services/            # ✅ Services API organisés
        │   ├── api.ts           # Client API de base
        │   ├── projects.ts      # Service projets
        │   └── analyses.ts      # Service analyses
        ├── types/               # ✅ Types TypeScript
        │   └── index.ts
        ├── stores/              # ✅ Gestion d'état
        └── utils/               # Utilitaires frontend
```

## 🚀 Démarrage rapide

1. **Setup backend** :
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup frontend** :
```bash
cd frontend
npm install
```

3. **Démarrage automatique** :
```bash
./start-dev.sh
```

## ✅ Avantages de cette structure

### **Backend organisé** :
- **`core/`** : Configuration centralisée et base de données
- **`schemas/`** : Validation Pydantic séparée des modèles
- **`crud/`** : Opérations base de données réutilisables
- **`api/v1/`** : API versionnée pour l'évolutivité
- **`services/`** : Logique métier découplée
- **`tests/`** : Tests organisés par module

### **Frontend maintenable** :
- **`components/ui/`** : Composants réutilisables (Button, Input...)
- **`pages/`** : Pages avec routing clair
- **`hooks/`** : Logique réutilisable (useProjects, useAnalyses...)
- **`services/`** : Appels API organisés par domaine
- **`types/`** : Types TypeScript centralisés
- **`stores/`** : État global géré proprement

### **DevOps simplifié** :
- **Docker Compose** : Environnement reproductible
- **Alembic** : Migrations versionnées
- **Variables d'env** : Configuration flexible
- **Tests** : Structure prête pour TDD

## 📝 Prochaines étapes

- [x] ✅ Structure projet professionnelle
- [x] ✅ Configuration Docker + Alembic
- [x] ✅ Architecture frontend modulaire
- [ ] 🔄 **Définir les modèles de base de données**
- [ ] 📡 Implémenter les endpoints API CRUD
- [ ] 🎨 Créer l'interface utilisateur
- [ ] 🤖 Intégrer les APIs des LLM
- [ ] 📊 Développer l'analyse automatique 
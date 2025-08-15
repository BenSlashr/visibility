# 📚 API Documentation - Visibility Tracker

## 🚀 Base URL
```
http://localhost:8021/api/v1
```

## 🔐 Authentication
Aucune authentification requise pour le moment (développement).

---

## 📋 **Endpoints Projets**

### Créer un Projet
```http
POST /projects/
```

**Body** :
```json
{
  "name": "Mon Site E-commerce",
  "main_website": "https://mon-site.com",
  "description": "Description du projet",
  "keywords": ["casques gaming", "écouteurs bluetooth"],
  "competitors": [
    {
      "name": "Amazon",
      "website": "https://amazon.fr"
    }
  ]
}
```

**Réponse** :
```json
{
  "id": "uuid",
  "name": "Mon Site E-commerce",
  "main_website": "https://mon-site.com",
  "description": "Description du projet",
  "created_at": "2025-01-27T12:30:00",
  "updated_at": "2025-01-27T12:30:00",
  "keywords": [
    {
      "keyword": "casques gaming",
      "created_at": "2025-01-27T12:30:00"
    }
  ],
  "competitors": [
    {
      "id": "uuid",
      "name": "Amazon", 
      "website": "https://amazon.fr",
      "created_at": "2025-01-27T12:30:00"
    }
  ]
}
```

### Lister les Projets
```http
GET /projects/?skip=0&limit=100
```

### Détails d'un Projet
```http
GET /projects/{project_id}
```

### Supprimer un Projet
```http
DELETE /projects/{project_id}
```

---

## 🧠 **Endpoints Modèles IA**

### Lister les Modèles IA
```http
GET /ai-models/?skip=0&limit=100
```

**Réponse** :
```json
[
  {
    "id": "uuid",
    "name": "ChatGPT-4o Latest",
    "provider": "openai",
    "model_identifier": "chatgpt-4o-latest",
    "max_tokens": 8192,
    "cost_per_1k_tokens": 0.005,
    "is_active": true,
    "created_at": "2025-01-27T12:00:00"
  },
  {
    "id": "uuid",
    "name": "Gemini 2.5 Flash",
    "provider": "google",
    "model_identifier": "gemini-2.0-flash-exp",
    "max_tokens": 8192,
    "cost_per_1k_tokens": 0.00015,
    "is_active": true,
    "created_at": "2025-01-27T12:00:00"
  }
]
```

### Modèles Actifs Uniquement
```http
GET /ai-models/active
```

---

## 📝 **Endpoints Prompts**

### Créer un Prompt
```http
POST /prompts/
```

**Body** :
```json
{
  "project_id": "uuid",
  "ai_model_id": "uuid",
  "name": "Test Recommandation Sites",
  "template": "Recommande-moi 3 sites web fiables pour acheter des {first_keyword}. Je cherche pour le projet {project_name}.",
  "description": "Description du prompt",
  "tags": ["test", "recommandation"],
  "is_active": true
}
```

**Variables disponibles dans les templates** :
- `{project_name}` : Nom du projet
- `{main_website}` : Site principal du projet
- `{first_keyword}` : Premier mot-clé du projet
- `{keywords_list}` : Liste complète des mots-clés

### Lister les Prompts
```http
GET /prompts/?skip=0&limit=100
```

### Prompts par Projet
```http
GET /prompts/project/{project_id}
```

### **Exécuter un Prompt** (🎯 ENDPOINT PRINCIPAL)
```http
POST /prompts/{prompt_id}/execute
```

**Body** (optionnel) :
```json
{
  "variables": {
    "custom_var": "valeur personnalisée"
  },
  "max_tokens": 150
}
```

**Réponse** :
```json
{
  "success": true,
  "analysis_id": "uuid",
  "ai_response": "1. Amazon : Amazon propose une large sélection...",
  "variables_used": {
    "project_name": "Mon Site E-commerce",
    "first_keyword": "casques gaming"
  },
  "brand_mentioned": false,
  "website_mentioned": false,
  "website_linked": false,
  "ranking_position": null,
  "ai_model_used": "GPT-3.5 Turbo",
  "tokens_used": 186,
  "processing_time_ms": 2094,
  "cost_estimated": 0.000279,
  "competitors_analysis": [
    {
      "competitor_name": "Amazon",
      "is_mentioned": true,
      "mention_context": "Amazon propose une large sélection...",
      "ranking_position": 1
    }
  ]
}
```

### Prévisualiser un Prompt
```http
POST /prompts/{prompt_id}/preview
```

### Valider un Prompt
```http
POST /prompts/{prompt_id}/validate
```

---

## 📊 **Endpoints Analyses**

### Lister les Analyses
```http
GET /analyses/?skip=0&limit=100
```

**Filtres disponibles** :
- `?project_id=uuid` : Analyses d'un projet
- `?prompt_id=uuid` : Analyses d'un prompt
- `?brand_mentioned=true` : Analyses avec mention de marque
- `?date_from=2025-01-01` : Analyses depuis une date

### Détails d'une Analyse
```http
GET /analyses/{analysis_id}
```

### Analyses Récentes
```http
GET /analyses/recent/{days}?limit=50
```

### Meilleures Performances
```http
GET /analyses/best-performing/{limit}
```

### Statistiques par Projet
```http
GET /analyses/stats/project/{project_id}
```

**Réponse** :
```json
{
  "project_id": "uuid",
  "project_name": "Mon Site E-commerce",
  "total_analyses": 25,
  "brand_mentions": 5,
  "website_mentions": 3,
  "website_links": 1,
  "average_visibility_score": 15.2,
  "total_cost": 0.0125,
  "total_tokens": 4500,
  "average_processing_time": 2500.0,
  "top_ranking_position": 2,
  "last_analysis": "2025-01-27T12:30:00"
}
```

### Statistiques Globales
```http
GET /analyses/stats/global
```

---

## 🎨 **Codes d'Erreur**

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Données invalides |
| 404 | Not Found | Ressource introuvable |
| 422 | Validation Error | Erreur de validation Pydantic |
| 500 | Internal Server Error | Erreur serveur |

**Format d'erreur** :
```json
{
  "error": true,
  "status_code": 404,
  "message": "Projet non trouvé",
  "path": "/api/v1/projects/invalid-id",
  "method": "GET"
}
```

---

## 🔄 **Workflow Typique Frontend**

### 1. Charger les Données Initiales
```javascript
// Charger projets et modèles IA
const projects = await fetch('/api/v1/projects/').then(r => r.json());
const aiModels = await fetch('/api/v1/ai-models/active').then(r => r.json());
```

### 2. Créer un Nouveau Projet
```javascript
const newProject = await fetch('/api/v1/projects/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Mon Nouveau Projet',
    main_website: 'https://mon-site.com',
    keywords: ['mot-clé 1', 'mot-clé 2'],
    competitors: [{ name: 'Concurrent', website: 'https://concurrent.com' }]
  })
}).then(r => r.json());
```

### 3. Créer et Exécuter un Prompt
```javascript
// Créer le prompt
const prompt = await fetch('/api/v1/prompts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_id: newProject.id,
    ai_model_id: aiModels[0].id,
    name: 'Test Visibility',
    template: 'Recommande des sites pour {first_keyword}',
    tags: ['test']
  })
}).then(r => r.json());

// Exécuter le prompt
const analysis = await fetch(`/api/v1/prompts/${prompt.id}/execute`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
}).then(r => r.json());

console.log('Visibilité détectée:', {
  brandMentioned: analysis.brand_mentioned,
  websiteMentioned: analysis.website_mentioned,
  cost: analysis.cost_estimated
});
```

### 4. Afficher les Statistiques
```javascript
const stats = await fetch(`/api/v1/analyses/stats/project/${projectId}`)
  .then(r => r.json());

// Afficher métriques dans le dashboard
updateDashboard({
  totalAnalyses: stats.total_analyses,
  visibilityScore: stats.average_visibility_score,
  totalCost: stats.total_cost
});
```

---

## 🎯 **Conseils d'Intégration Frontend**

### État de Chargement
```javascript
// Exécution de prompt peut prendre 2-5 secondes
setLoading(true);
const result = await executePrompt(promptId);
setLoading(false);
```

### Gestion d'Erreurs
```javascript
try {
  const response = await fetch('/api/v1/prompts/invalid/execute', {
    method: 'POST'
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }
} catch (error) {
  console.error('Erreur API:', error.message);
  showNotification('Erreur lors de l\'exécution', 'error');
}
```

### Polling pour Analyses Longues
```javascript
// Pour des analyses très longues (non implémenté mais prévu)
const pollAnalysis = async (analysisId) => {
  const response = await fetch(`/api/v1/analyses/${analysisId}`);
  const analysis = await response.json();
  
  if (analysis.status === 'processing') {
    setTimeout(() => pollAnalysis(analysisId), 2000);
  } else {
    displayResults(analysis);
  }
};
```

---

## 📱 **Format Réponses pour UI**

### Card Projet
```json
{
  "id": "uuid",
  "name": "Mon Site E-commerce", 
  "keywordCount": 5,
  "competitorCount": 3,
  "lastAnalysis": "2025-01-27T12:30:00",
  "totalAnalyses": 15,
  "visibilityScore": 25.5
}
```

### Card Analyse
```json
{
  "id": "uuid",
  "promptName": "Test Recommandation",
  "aiModel": "GPT-4o Latest",
  "executedAt": "2025-01-27T12:30:00",
  "brandMentioned": true,
  "websiteMentioned": false,
  "cost": 0.000279,
  "processingTime": "2.1s"
}
```

Le backend est prêt pour une intégration frontend fluide ! 🚀 
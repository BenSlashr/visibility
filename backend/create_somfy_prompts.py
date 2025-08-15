import requests
import json

# Configuration
BASE_URL = "http://localhost:8021/api/v1"
PROJECT_ID = "f04a7bdab4a84c7eafc7be17b5d67a62"  # Somfy
AI_MODEL_ID = "deb05bca2ce14d32b78b413b55c5b3b1"  # GPT-4o

# Prompts pour Somfy - gamme complète de domotique
prompts_data = [
    # Volets roulants et stores
    {
        "name": "Recommandations sites volets roulants électriques",
        "template": "Recommande-moi des sites pour acheter des volets roulants électriques. Je cherche des solutions fiables avec un bon rapport qualité-prix pour équiper ma maison.",
        "description": "Recherche de sites e-commerce pour volets roulants électriques"
    },
    {
        "name": "Meilleures marques volets roulants",
        "template": "Quelles sont les meilleures marques de volets roulants électriques en 2024 ? Je veux connaître les fabricants les plus réputés pour la qualité et la durabilité.",
        "description": "Comparatif des marques de volets roulants électriques"
    },
    {
        "name": "Recommandations sites stores extérieurs",
        "template": "Recommande-moi des sites pour acheter des stores extérieurs motorisés. Je cherche des solutions pour ma terrasse avec protection solaire et résistance au vent.",
        "description": "Recherche de sites pour stores extérieurs motorisés"
    },
    {
        "name": "Meilleures marques stores extérieurs",
        "template": "Quelles sont les meilleures marques de stores extérieurs motorisés ? Je veux des marques reconnues pour leur robustesse et leurs systèmes de motorisation.",
        "description": "Comparatif des marques de stores extérieurs"
    },
    
    # Portails et portes de garage
    {
        "name": "Recommandations sites portails automatiques",
        "template": "Recommande-moi des sites pour acheter des portails automatiques. Je cherche des solutions complètes avec motorisation et système de sécurité intégré.",
        "description": "Recherche de sites pour portails automatiques"
    },
    {
        "name": "Meilleures marques portails automatiques",
        "template": "Quelles sont les meilleures marques de portails automatiques en France ? Je veux connaître les fabricants leaders pour la motorisation de portails.",
        "description": "Comparatif des marques de portails automatiques"
    },
    {
        "name": "Recommandations sites portes garage motorisées",
        "template": "Recommande-moi des sites pour acheter des portes de garage motorisées. Je cherche des solutions sectionnelles ou basculantes avec télécommande.",
        "description": "Recherche de sites pour portes de garage motorisées"
    },
    {
        "name": "Meilleures marques portes garage",
        "template": "Quelles sont les meilleures marques de portes de garage motorisées ? Je veux des marques fiables avec de bons systèmes de motorisation.",
        "description": "Comparatif des marques de portes de garage"
    },
    
    # Domotique et maison connectée
    {
        "name": "Recommandations sites domotique maison",
        "template": "Recommande-moi des sites pour acheter des systèmes de domotique pour la maison. Je cherche des solutions complètes pour automatiser volets, éclairage et chauffage.",
        "description": "Recherche de sites pour systèmes domotique"
    },
    {
        "name": "Meilleures marques domotique",
        "template": "Quelles sont les meilleures marques de domotique résidentielle en 2024 ? Je veux des systèmes compatibles et évolutifs pour ma maison connectée.",
        "description": "Comparatif des marques de domotique"
    },
    {
        "name": "Recommandations sites box domotique",
        "template": "Recommande-moi des sites pour acheter une box domotique. Je cherche un hub central pour contrôler tous mes équipements automatisés.",
        "description": "Recherche de sites pour box domotique"
    },
    {
        "name": "Meilleures marques box domotique",
        "template": "Quelles sont les meilleures marques de box domotique ? Je veux une solution centrale fiable pour piloter ma maison connectée.",
        "description": "Comparatif des marques de box domotique"
    },
    
    # Motorisation et accessoires
    {
        "name": "Recommandations sites moteurs volets",
        "template": "Recommande-moi des sites pour acheter des moteurs pour volets roulants. Je cherche des moteurs de remplacement fiables et silencieux.",
        "description": "Recherche de sites pour moteurs de volets"
    },
    {
        "name": "Meilleures marques moteurs volets",
        "template": "Quelles sont les meilleures marques de moteurs pour volets roulants ? Je veux des moteurs durables avec faible consommation électrique.",
        "description": "Comparatif des marques de moteurs pour volets"
    },
    {
        "name": "Recommandations sites télécommandes domotique",
        "template": "Recommande-moi des sites pour acheter des télécommandes domotique universelles. Je cherche des télécommandes compatibles avec plusieurs marques.",
        "description": "Recherche de sites pour télécommandes domotique"
    },
    {
        "name": "Meilleures marques télécommandes",
        "template": "Quelles sont les meilleures marques de télécommandes pour domotique ? Je veux des télécommandes fiables avec bonne portée.",
        "description": "Comparatif des marques de télécommandes"
    },
    
    # Sécurité et alarmes
    {
        "name": "Recommandations sites alarmes maison",
        "template": "Recommande-moi des sites pour acheter des systèmes d'alarme connectés. Je cherche des solutions complètes avec détecteurs et caméras.",
        "description": "Recherche de sites pour alarmes connectées"
    },
    {
        "name": "Meilleures marques alarmes connectées",
        "template": "Quelles sont les meilleures marques d'alarmes connectées pour la maison ? Je veux des systèmes fiables avec application mobile.",
        "description": "Comparatif des marques d'alarmes connectées"
    },
    
    # Éclairage connecté
    {
        "name": "Recommandations sites éclairage connecté",
        "template": "Recommande-moi des sites pour acheter de l'éclairage connecté. Je cherche des ampoules et interrupteurs pilotables à distance.",
        "description": "Recherche de sites pour éclairage connecté"
    },
    {
        "name": "Meilleures marques éclairage connecté",
        "template": "Quelles sont les meilleures marques d'éclairage connecté ? Je veux des solutions compatibles avec les assistants vocaux.",
        "description": "Comparatif des marques d'éclairage connecté"
    }
]

def create_prompt(prompt_data):
    """Crée un prompt via l'API"""
    url = f"{BASE_URL}/prompts/"
    
    payload = {
        "project_id": PROJECT_ID,
        "ai_model_id": AI_MODEL_ID,
        "name": prompt_data["name"],
        "template": prompt_data["template"],
        "description": prompt_data["description"],
        "is_active": True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Prompt créé: {prompt_data['name']}")
            return result
        else:
            print(f"❌ Erreur création prompt {prompt_data['name']}: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception pour {prompt_data['name']}: {str(e)}")
        return None

# Créer tous les prompts
print(f"🚀 Création de {len(prompts_data)} prompts pour Somfy...")
print(f"📁 Projet ID: {PROJECT_ID}")
print(f"🤖 Modèle IA: {AI_MODEL_ID}")
print("-" * 50)

created_count = 0
for i, prompt_data in enumerate(prompts_data, 1):
    print(f"[{i}/{len(prompts_data)}] Création: {prompt_data['name']}")
    result = create_prompt(prompt_data)
    if result:
        created_count += 1

print("-" * 50)
print(f"🎉 Terminé! {created_count}/{len(prompts_data)} prompts créés avec succès")

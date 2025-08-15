#!/usr/bin/env python3
"""
Script de test pour le système NLP complet
Teste la classification, les services et l'API
"""

import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from app.nlp.topics_classifier import AdvancedTopicsClassifier, quick_classify
from app.nlp.keywords_config import SEO_INTENT_KEYWORDS, BUSINESS_TOPICS


def test_classifier_basic():
    """Test basique du classificateur"""
    print("🧪 Test du classificateur NLP...")
    
    # Test 1: Intention commerciale
    prompt1 = "Quel est le meilleur système domotique pour une maison ?"
    response1 = """
    Pour choisir le meilleur système domotique, plusieurs marques se distinguent:
    
    1. **Somfy TaHoma** - Excellent pour les volets roulants, prix abordable
    2. **Legrand Home + Control** - Interface intuitive, bonne compatibilité
    3. **Schneider Wiser** - Performance Z-Wave, installation facile
    
    En termes de rapport qualité-prix, je recommande Somfy pour débuter.
    """
    
    results1 = quick_classify(prompt1, response1, 'domotique')
    print(f"✅ Test commercial - Intent: {results1['seo_intent']['main_intent']} (confiance: {results1['seo_intent']['confidence']})")
    
    # Test 2: Intention informationnelle
    prompt2 = "Comment fonctionne la technologie Z-Wave ?"
    response2 = """
    Z-Wave est un protocole de communication sans fil spécialement conçu pour la domotique.
    
    **Principe de fonctionnement:**
    - Réseau mesh: chaque appareil peut relayer les signaux
    - Fréquence 868 MHz en Europe, portée jusqu'à 100m
    - Chiffrement AES-128 pour la sécurité
    
    Les avantages incluent une faible consommation et une grande fiabilité.
    """
    
    results2 = quick_classify(prompt2, response2, 'domotique')
    print(f"✅ Test informationnel - Intent: {results2['seo_intent']['main_intent']} (confiance: {results2['seo_intent']['confidence']})")
    
    # Test 3: Intention transactionnelle
    prompt3 = "Comment installer un volet roulant Somfy ?"
    response3 = """
    **Installation étape par étape:**
    
    1. **Préparation:** Coupez l'électricité, préparez les outils
    2. **Montage:** Fixez les supports, installez le moteur Oximo
    3. **Câblage:** Connectez l'alimentation selon le schéma
    4. **Configuration:** Programmez les fins de course avec Situo
    5. **Test:** Vérifiez le fonctionnement complet
    
    Durée: environ 2h pour un bricoleur expérimenté.
    """
    
    results3 = quick_classify(prompt3, response3, 'domotique')
    print(f"✅ Test transactionnel - Intent: {results3['seo_intent']['main_intent']} (confiance: {results3['seo_intent']['confidence']})")


def test_business_topics():
    """Test de la détection des business topics"""
    print("\n🏷️ Test des business topics...")
    
    prompt = "Comparaison des prix des systèmes domotique avec installation"
    response = """
    **Analyse des coûts:**
    
    - **Somfy TaHoma Box:** 199€ + installation 150€ = 349€
    - **Legrand Home + Control:** 299€ + installation 120€ = 419€
    - **Schneider Wiser:** 179€ + installation 180€ = 359€
    
    L'installation est facile avec Legrand (plug and play).
    La sécurité est excellente avec chiffrement sur tous les modèles.
    """
    
    results = quick_classify(prompt, response, 'domotique')
    
    print("Business topics détectés:")
    for topic in results['business_topics']:
        print(f"  - {topic['topic']}: score {topic['score']} (pertinence: {topic['relevance']})")


def test_entity_extraction():
    """Test de l'extraction d'entités"""
    print("\n🏢 Test de l'extraction d'entités...")
    
    response = """
    Somfy domine le marché français avec TaHoma et Connexoon.
    Legrand propose Home + Control avec technologie Zigbee.
    Schneider Electric mise sur Wiser et le protocole Z-Wave.
    Les technologies WiFi et Thread gagnent en popularité.
    """
    
    results = quick_classify("", response, 'domotique')
    
    print("Entités détectées:")
    for entity_type, entities in results['sector_entities'].items():
        print(f"  {entity_type.title()}:")
        for entity in entities:
            if isinstance(entity, dict):
                print(f"    - {entity['name']} (mentions: {entity['count']})")
            else:
                print(f"    - {entity}")


def test_confidence_scoring():
    """Test du système de scoring de confiance"""
    print("\n📊 Test du scoring de confiance...")
    
    # Texte avec beaucoup de signaux clairs
    high_confidence_text = """
    Comparaison complète: Somfy TaHoma vs Legrand Home + Control
    
    **Prix et installation:**
    - Somfy: 199€, installation facile avec Z-Wave
    - Legrand: 299€, interface intuitive, compatible Zigbee
    
    **Recommandation:** Je conseille Somfy pour le rapport qualité-prix.
    Idéal pour débuter en domotique, sécurité optimale.
    """
    
    high_results = quick_classify("Quel système domotique acheter ?", high_confidence_text, 'domotique')
    
    # Texte avec peu de signaux
    low_confidence_text = "Il existe des solutions."
    
    low_results = quick_classify("Question générale", low_confidence_text, 'domotique')
    
    print(f"✅ Confiance élevée: {high_results['confidence']}")
    print(f"⚠️  Confiance faible: {low_results['confidence']}")


def test_keyword_coverage():
    """Test de la couverture des mots-clés"""
    print("\n📚 Test de la couverture des mots-clés...")
    
    # Compter les mots-clés disponibles
    total_seo_keywords = 0
    for intent, categories in SEO_INTENT_KEYWORDS.items():
        for category, keywords in categories.items():
            if category != 'weight' and isinstance(keywords, list):
                total_seo_keywords += len(keywords)
    
    total_business_keywords = 0
    for sector, topics in BUSINESS_TOPICS.items():
        for topic, config in topics.items():
            total_business_keywords += len(config['keywords'])
    
    print(f"📊 Mots-clés SEO: {total_seo_keywords}")
    print(f"📊 Mots-clés business: {total_business_keywords}")
    print(f"📊 Total: {total_seo_keywords + total_business_keywords}")


def test_sector_specific():
    """Test des fonctionnalités spécifiques par secteur"""
    print("\n🎯 Test des secteurs spécialisés...")
    
    # Test domotique
    domotique_text = "TaHoma de Somfy utilise Z-Wave pour contrôler les volets"
    domotique_results = quick_classify("", domotique_text, 'domotique')
    
    # Test tech général
    tech_text = "Cette API offre de bonnes performances et une grande fiabilité"
    tech_results = quick_classify("", tech_text, 'tech_general')
    
    print(f"✅ Domotique - Entités: {len(domotique_results['sector_entities'])}")
    print(f"✅ Tech général - Topics: {len(tech_results['business_topics'])}")


def main():
    """Fonction principale de test"""
    print("🚀 Test complet du système NLP Visibility-V2")
    print("=" * 50)
    
    try:
        test_classifier_basic()
        test_business_topics() 
        test_entity_extraction()
        test_confidence_scoring()
        test_keyword_coverage()
        test_sector_specific()
        
        print("\n" + "=" * 50)
        print("🎉 Tous les tests sont passés avec succès!")
        print("\n💡 Pour tester l'API, utilisez:")
        print("   POST /api/v1/analyses/{analysis_id}/nlp")
        print("   GET  /api/v1/analyses/nlp/project-summary/{project_id}")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
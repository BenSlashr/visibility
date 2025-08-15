#!/usr/bin/env python3
"""
Test détaillé du système NLP avec des cas réels
"""

import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

from app.nlp.topics_classifier import AdvancedTopicsClassifier

def test_real_scenarios():
    """Test avec des scénarios réels d'utilisation"""
    
    classifier = AdvancedTopicsClassifier('domotique')
    
    # Scénario 1: Question commerciale complexe
    print("🎯 Test Scénario Commercial Complexe")
    prompt1 = "Somfy TaHoma vs Legrand Home + Control : lequel choisir pour une maison de 150m² ?"
    response1 = """
    **Comparaison détaillée Somfy TaHoma vs Legrand Home + Control**
    
    Pour une maison de 150m², voici mon analyse :
    
    **💰 Prix et investissement :**
    - Somfy TaHoma Switch : 199€ + modules Z-Wave (comptez 50€/pièce)
    - Legrand Home + Control : 299€ + modules Zigbee (40€/pièce en moyenne)
    
    **⚙️ Installation et facilité :**
    - TaHoma : installation plus technique, mais excellente compatibilité
    - Home + Control : plus plug and play, interface très intuitive
    
    **🔒 Sécurité et fiabilité :**
    - Somfy : chiffrement AES-256, très robuste
    - Legrand : sécurité correcte, mise à jour régulière
    
    **🏆 Recommandation :**
    Pour votre maison, je recommande **Somfy TaHoma** pour le rapport qualité-prix. 
    C'est le choix idéal si vous acceptez une courbe d'apprentissage légèrement plus élevée.
    """
    
    results1 = classifier.classify_full(prompt1, response1)
    
    print(f"✅ Intention SEO: {results1['seo_intent']['main_intent']} (confiance: {results1['seo_intent']['confidence']})")
    print(f"📊 Business topics détectés: {len(results1['business_topics'])}")
    for topic in results1['business_topics'][:3]:
        print(f"   - {topic['topic']}: {topic['score']} ({topic['relevance']})")
    print(f"🏢 Entités: {len(results1['sector_entities'])} types")
    print(f"🎯 Confiance globale: {results1['confidence']}")
    
    # Scénario 2: Question technique informationnelle  
    print("\n🔧 Test Scénario Technique")
    prompt2 = "Comment fonctionne la technologie Z-Wave dans la domotique ?"
    response2 = """
    **Z-Wave : le protocole mesh pour la domotique**
    
    Z-Wave est un protocole de communication sans fil spécialement conçu pour les maisons connectées :
    
    **⚡ Caractéristiques techniques :**
    - Fréquence : 868 MHz en Europe (évite les interférences WiFi)
    - Portée : jusqu'à 100m en extérieur, 30m en intérieur
    - Réseau mesh : chaque appareil fait relais
    - Consommation : très faible, idéal pour capteurs sur pile
    
    **🔒 Sécurité :**
    - Chiffrement AES-128 par défaut
    - Authentification des appareils
    - Clés de chiffrement uniques par réseau
    
    **🏠 Utilisation pratique :**
    Compatible avec Somfy TaHoma, Fibaro, Vera, etc.
    Parfait pour volets roulants, éclairage, capteurs.
    """
    
    results2 = classifier.classify_full(prompt2, response2)
    
    print(f"✅ Intention SEO: {results2['seo_intent']['main_intent']} (confiance: {results2['seo_intent']['confidence']})")
    print(f"📊 Business topics: {len(results2['business_topics'])}")
    print(f"🔧 Type de contenu: {results2['content_type']['main_type']} (confiance: {results2['content_type']['confidence']})")
    
    # Scénario 3: Guide d'installation (transactionnel)
    print("\n🛠️ Test Scénario Installation")
    prompt3 = "Comment installer et configurer un volet roulant Somfy Oximo IO ?"
    response3 = """
    **Guide d'installation Somfy Oximo IO étape par étape**
    
    **🔧 Étape 1 : Préparation**
    - Coupez l'électricité au disjoncteur
    - Préparez les outils : perceuse, niveau, tournevis
    - Vérifiez la compatibilité avec votre coffre
    
    **⚙️ Étape 2 : Montage mécanique**
    - Fixez les supports dans le coffre
    - Installez le moteur Oximo dans le tube d'enroulement
    - Vérifiez l'alignement avec un niveau
    
    **🔌 Étape 3 : Raccordement électrique**
    - Connectez phase, neutre et terre selon le schéma
    - Respectez les codes couleur
    - Utilisez des dominos de qualité
    
    **📱 Étape 4 : Configuration IO**
    - Appuyez 2 secondes sur le bouton PROG du moteur
    - Programmez la télécommande Situo
    - Réglez les fins de course avec les flèches
    
    **✅ Test final :**
    Testez plusieurs cycles complets pour vérifier le bon fonctionnement.
    """
    
    results3 = classifier.classify_full(prompt3, response3)
    
    print(f"✅ Intention SEO: {results3['seo_intent']['main_intent']} (confiance: {results3['seo_intent']['confidence']})")
    print(f"🛠️ Type de contenu: {results3['content_type']['main_type']}")
    print(f"📋 Mots-clés sémantiques: {results3['semantic_keywords'][:10]}")


def test_edge_cases():
    """Test des cas limites"""
    print("\n🚨 Test des cas limites")
    
    classifier = AdvancedTopicsClassifier('domotique')
    
    # Cas 1: Texte très court
    short_results = classifier.classify_full("Prix ?", "Cher.")
    print(f"📏 Texte court - Confiance: {short_results['confidence']}")
    
    # Cas 2: Texte sans rapport avec la domotique
    offtopic_results = classifier.classify_full(
        "Recette de cuisine", 
        "Mélangez les œufs avec la farine et ajoutez le sucre."
    )
    print(f"🍳 Hors sujet - Confiance: {offtopic_results['confidence']}")
    print(f"   Intention détectée: {offtopic_results['seo_intent']['main_intent']}")
    
    # Cas 3: Texte multilingue
    multilang_results = classifier.classify_full(
        "Best smart home system?",
        "Somfy is excellent for price quality ratio. Very good installation process."
    )
    print(f"🌍 Multilingue - Confiance: {multilang_results['confidence']}")


def test_detailed_scoring():
    """Test détaillé du système de scoring"""
    print("\n📊 Test détaillé du scoring")
    
    classifier = AdvancedTopicsClassifier('domotique')
    
    text_with_many_signals = """
    Comparaison prix Somfy vs Legrand : 
    - TaHoma coûte 199€, installation facile
    - Home + Control prix 299€, interface intuitive
    Je recommande Somfy pour le rapport qualité-prix.
    Excellent choix pour débuter en domotique.
    Compatible Z-Wave et Zigbee.
    """
    
    results = classifier.classify_full("Quel système acheter ?", text_with_many_signals)
    
    print("🎯 Analyse détaillée des scores SEO:")
    for intent, score in results['seo_intent']['all_scores'].items():
        print(f"   {intent}: {score}")
    
    print("\n📋 Matches détaillés:")
    for match in results['seo_intent']['detailed_matches']:
        print(f"   Catégorie: {match['category']} (score: {match['score']})")
        for keyword_match in match['matches'][:3]:  # Top 3
            print(f"     - '{keyword_match['keyword']}': {keyword_match['count']} fois")


if __name__ == "__main__":
    print("🧪 Test détaillé du système NLP")
    print("=" * 60)
    
    try:
        test_real_scenarios()
        test_edge_cases()
        test_detailed_scoring()
        
        print("\n" + "=" * 60)
        print("🎉 Tests détaillés terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
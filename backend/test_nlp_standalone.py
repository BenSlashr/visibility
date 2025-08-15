#!/usr/bin/env python3
"""
Test standalone du système NLP sans dépendances externes
"""

import sys
import json
from pathlib import Path

# Test d'import des modules NLP uniquement
def test_nlp_imports():
    """Test d'import des modules NLP"""
    print("📦 Test des imports NLP...")
    
    try:
        # Test import configuration
        sys.path.append(str(Path(__file__).parent))
        from app.nlp.keywords_config import (
            SEO_INTENT_KEYWORDS, 
            BUSINESS_TOPICS,
            SECTOR_SPECIFIC_KEYWORDS,
            FRENCH_EXPRESSIONS,
            SCORING_CONFIG
        )
        print("✅ Configuration des mots-clés importée")
        
        # Test import classificateur
        from app.nlp.topics_classifier import AdvancedTopicsClassifier, quick_classify
        print("✅ Classificateur importé")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_keywords_quality():
    """Test de la qualité des dictionnaires de mots-clés"""
    print("\n📚 Test de la qualité des mots-clés...")
    
    try:
        from app.nlp.keywords_config import SEO_INTENT_KEYWORDS, BUSINESS_TOPICS
        
        # Vérifier les intentions SEO
        required_intents = ['commercial', 'informational', 'transactional', 'navigational']
        available_intents = list(SEO_INTENT_KEYWORDS.keys())
        
        print(f"✅ Intentions SEO: {available_intents}")
        
        missing_intents = set(required_intents) - set(available_intents)
        if missing_intents:
            print(f"❌ Intentions manquantes: {missing_intents}")
            return False
        
        # Compter les mots-clés par intention
        for intent, categories in SEO_INTENT_KEYWORDS.items():
            total_keywords = 0
            for category, keywords in categories.items():
                if category != 'weight' and isinstance(keywords, list):
                    total_keywords += len(keywords)
            
            weight = categories.get('weight', 1.0)
            print(f"   - {intent}: {total_keywords} mots-clés (poids: {weight})")
        
        # Vérifier les secteurs business
        available_sectors = list(BUSINESS_TOPICS.keys())
        print(f"✅ Secteurs disponibles: {available_sectors}")
        
        for sector, topics in BUSINESS_TOPICS.items():
            print(f"   - {sector}: {len(topics)} topics")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test qualité: {e}")
        return False


def test_classifier_functionality():
    """Test des fonctionnalités du classificateur"""
    print("\n🧠 Test du classificateur...")
    
    try:
        from app.nlp.topics_classifier import AdvancedTopicsClassifier
        
        # Test d'initialisation
        classifier = AdvancedTopicsClassifier('domotique')
        print("✅ Classificateur initialisé pour secteur domotique")
        
        # Test de classification basique
        prompt = "Quel est le meilleur système domotique ?"
        response = "Somfy TaHoma offre un excellent rapport qualité-prix avec une installation facile."
        
        results = classifier.classify_full(prompt, response)
        
        # Vérifier la structure des résultats
        required_keys = [
            'seo_intent', 'business_topics', 'content_type', 
            'sector_entities', 'semantic_keywords', 'confidence'
        ]
        
        for key in required_keys:
            if key not in results:
                print(f"❌ Clé manquante dans résultats: {key}")
                return False
        
        print("✅ Structure des résultats correcte")
        
        # Vérifier les valeurs
        seo_intent = results['seo_intent']
        if 'main_intent' not in seo_intent or 'confidence' not in seo_intent:
            print("❌ Structure seo_intent incorrecte")
            return False
        
        confidence = results['confidence']
        if not (0 <= confidence <= 1):
            print(f"❌ Confiance hors limites: {confidence}")
            return False
        
        print(f"✅ Classification réussie:")
        print(f"   - Intent: {seo_intent['main_intent']} (confiance: {seo_intent['confidence']})")
        print(f"   - Confiance globale: {confidence}")
        print(f"   - Business topics: {len(results['business_topics'])}")
        print(f"   - Type de contenu: {results['content_type']['main_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test classificateur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test des cas limites"""
    print("\n🚨 Test des cas limites...")
    
    try:
        from app.nlp.topics_classifier import quick_classify
        
        # Cas 1: Texte vide
        empty_results = quick_classify("", "", 'domotique')
        print(f"✅ Texte vide - Confiance: {empty_results['confidence']}")
        
        # Cas 2: Texte très court
        short_results = quick_classify("Prix ?", "200€", 'domotique')
        print(f"✅ Texte court - Intent: {short_results['seo_intent']['main_intent']}")
        
        # Cas 3: Texte sans mots-clés spécialisés
        generic_results = quick_classify(
            "Question générale", 
            "Ceci est un texte générique sans termes spécialisés",
            'domotique'
        )
        print(f"✅ Texte générique - Confiance: {generic_results['confidence']}")
        
        # Cas 4: Texte avec beaucoup de signaux
        rich_results = quick_classify(
            "Comparaison prix installation Somfy TaHoma vs Legrand",
            "Somfy coûte 199€ avec installation Z-Wave facile. Je recommande ce choix pour le rapport qualité prix.",
            'domotique'
        )
        print(f"✅ Texte riche - Confiance: {rich_results['confidence']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test cas limites: {e}")
        return False


def test_performance():
    """Test de performance basique"""
    print("\n⚡ Test de performance...")
    
    try:
        import time
        from app.nlp.topics_classifier import quick_classify
        
        # Texte de test
        prompt = "Comment choisir le meilleur système domotique pour sa maison ?"
        response = """
        Pour choisir le bon système domotique, plusieurs critères sont importants :
        
        1. Prix et budget : comptez entre 200€ et 500€ pour débuter
        2. Facilité d'installation : Legrand est plus plug and play
        3. Compatibilité : Z-Wave et Zigbee sont les standards
        4. Marques fiables : Somfy, Legrand, Schneider Electric
        5. Évolutivité : choisir un système extensible
        
        Je recommande Somfy TaHoma pour débuter avec un bon rapport qualité-prix.
        """
        
        # Test de vitesse
        start_time = time.time()
        num_tests = 10
        
        for i in range(num_tests):
            results = quick_classify(prompt, response, 'domotique')
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # en ms
        avg_time = total_time / num_tests
        
        print(f"✅ Performance test ({num_tests} classifications):")
        print(f"   - Temps total: {total_time:.1f}ms")
        print(f"   - Temps moyen: {avg_time:.1f}ms par classification")
        print(f"   - Débit: {1000/avg_time:.0f} classifications/seconde")
        
        # Vérifier que c'est dans les limites acceptables (< 100ms)
        if avg_time > 100:
            print(f"⚠️  Performance dégradée (> 100ms)")
        else:
            print(f"✅ Performance excellente (< 100ms)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test performance: {e}")
        return False


def main():
    """Test complet standalone"""
    print("🧪 Test Standalone NLP - Visibility-V2")
    print("=" * 50)
    
    tests = [
        ("Imports NLP", test_nlp_imports),
        ("Qualité mots-clés", test_keywords_quality),
        ("Classificateur", test_classifier_functionality),
        ("Cas limites", test_edge_cases),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Système NLP entièrement fonctionnel!")
        print("✨ Prêt pour l'intégration avec l'API Visibility-V2")
        print("\n💡 Prochaines étapes:")
        print("   1. Démarrer l'API backend")
        print("   2. Tester les endpoints /api/v1/analyses/*/nlp")
        print("   3. Vérifier l'analyse automatique des nouvelles données")
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
        print("Vérifiez les erreurs ci-dessus avant déploiement")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
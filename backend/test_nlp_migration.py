#!/usr/bin/env python
"""
Script de test de non-régression pour la migration NLP
Vérifie que toutes les fonctionnalités NLP continuent de fonctionner après migration
"""

import sys
import traceback
from typing import Dict, Any, List

# Ajouter le répertoire courant au path
sys.path.append('.')

def test_imports() -> bool:
    """Test que tous les imports critiques fonctionnent"""
    print("🔍 Test des imports critiques...")
    try:
        from app.nlp.adapters.legacy_adapter import legacy_nlp_service
        from app.api.v1.endpoints.analyses import router
        from app.services.execution_service import execution_service
        print("✅ Tous les imports fonctionnent")
        return True
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_legacy_adapter() -> bool:
    """Test des fonctions de base de l'adapter"""
    print("\n🔍 Test de l'adapter legacy...")
    try:
        from app.nlp.adapters.legacy_adapter import legacy_nlp_service
        
        # Test secteurs disponibles
        sectors = legacy_nlp_service.get_available_sectors()
        assert isinstance(sectors, list)
        assert len(sectors) > 0
        print(f"✅ Secteurs disponibles: {sectors}")
        
        # Test avec DB mockée pour éviter les erreurs DB
        class MockDB:
            def query(self, model):
                return MockQuery()
            def func(self):
                return MockFunc()
        
        class MockQuery:
            def count(self):
                return 100
            def filter(self, *args):
                return self
            def group_by(self, *args):
                return self
            def all(self):
                return []
            def scalar(self):
                return 0.75
        
        class MockFunc:
            def count(self, *args):
                return MockQuery()
            def avg(self, *args):
                return MockQuery()
        
        mock_db = MockDB()
        
        # Test stats globales
        stats = legacy_nlp_service.get_global_nlp_stats(mock_db)
        assert isinstance(stats, dict)
        required_keys = ['total_analyses', 'analyzed_with_nlp', 'nlp_coverage']
        for key in required_keys:
            assert key in stats
        print("✅ Stats globales fonctionnent")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur adapter: {e}")
        traceback.print_exc()
        return False

def test_database_integration() -> bool:
    """Test de l'intégration avec la vraie base de données"""
    print("\n🔍 Test intégration base de données...")
    try:
        from app.core.database import get_db
        from app.nlp.adapters.legacy_adapter import legacy_nlp_service
        from app.models.analysis import Analysis
        
        # Obtenir une session DB
        db = next(get_db())
        
        # Test stats globales
        stats = legacy_nlp_service.get_global_nlp_stats(db)
        print(f"✅ Stats globales: {stats['total_analyses']} analyses")
        
        # Test avec une analyse existante si disponible
        analysis = db.query(Analysis).first()
        if analysis:
            topics = legacy_nlp_service.get_analysis_topics(db, analysis.id)
            if topics:
                print(f"✅ Topics trouvés pour analyse {analysis.id[:8]}: {topics.seo_intent}")
            else:
                print(f"ℹ️  Aucun topic pour analyse {analysis.id[:8]} (normal)")
        else:
            print("ℹ️  Aucune analyse dans la DB")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur DB integration: {e}")
        return False

def test_execution_service() -> bool:
    """Test que l'execution service utilise bien le nouvel adapter"""
    print("\n🔍 Test integration execution service...")
    try:
        from app.services.execution_service import execution_service
        
        # Vérifier que l'import utilise bien le legacy adapter
        import inspect
        source = inspect.getsource(execution_service.__class__)
        
        if 'legacy_nlp_service' in source:
            print("✅ Execution service utilise le legacy adapter")
            return True
        else:
            print("⚠️  Execution service n'utilise pas le legacy adapter")
            return False
            
    except Exception as e:
        print(f"❌ Erreur execution service: {e}")
        return False

def test_endpoints_compatibility() -> bool:
    """Test que les endpoints utilisent bien l'adapter"""
    print("\n🔍 Test compatibilité endpoints...")
    try:
        from app.api.v1.endpoints.analyses import router
        import inspect
        
        # Récupérer le code source du module
        import app.api.v1.endpoints.analyses as analyses_module
        source = inspect.getsource(analyses_module)
        
        if 'legacy_nlp_service' in source:
            print("✅ Endpoints utilisent le legacy adapter")
            return True
        else:
            print("⚠️  Endpoints n'utilisent pas le legacy adapter")
            return False
            
    except Exception as e:
        print(f"❌ Erreur endpoints: {e}")
        return False

def run_all_tests() -> Dict[str, bool]:
    """Exécute tous les tests et retourne les résultats"""
    print("🚀 DÉBUT DES TESTS DE MIGRATION NLP\n")
    
    tests = {
        'imports': test_imports(),
        'legacy_adapter': test_legacy_adapter(),
        'database_integration': test_database_integration(),
        'execution_service': test_execution_service(),
        'endpoints_compatibility': test_endpoints_compatibility()
    }
    
    print(f"\n{'='*50}")
    print("📊 RÉSULTATS DES TESTS")
    print(f"{'='*50}")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 MIGRATION RÉUSSIE ! Tous les tests passent.")
        print("💡 La fonctionnalité NLP continue de fonctionner normalement.")
    else:
        print("⚠️  Certains tests ont échoué. Vérification recommandée.")
    
    return tests

if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit code pour CI/CD
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
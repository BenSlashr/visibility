#!/usr/bin/env python3
"""
Script de débogage pour identifier l'erreur CURRENT_TIMESTAMP
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.execution_service import ExecutionService
from app.crud.prompt import prompt as crud_prompt

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_execution():
    """Debug de l'exécution d'un prompt"""
    db = SessionLocal()
    
    try:
        # ID du prompt créé précédemment
        prompt_id = "ef18a6d30aeb4418b27d396c92570cd6"
        
        # Récupérer le prompt
        prompt = crud_prompt.get_with_relations(db, prompt_id)
        if not prompt:
            print(f"❌ Prompt {prompt_id} non trouvé")
            return
            
        print(f"✅ Prompt trouvé: {prompt.name}")
        print(f"✅ Projet: {prompt.project.name if prompt.project else 'N/A'}")
        print(f"✅ Modèle IA: {prompt.ai_model.name if prompt.ai_model else 'N/A'}")
        
        # Test du service d'exécution
        execution_service = ExecutionService()
        
        print("🔍 Test de l'exécution...")
        result = await execution_service.execute_prompt_analysis(db, prompt_id)
        
        print("✅ Exécution réussie!")
        print(f"Analyse ID: {result.get('analysis_id')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_execution()) 
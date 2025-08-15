#!/usr/bin/env python3
"""
Test complet du workflow : Création projet -> Prompt -> Exécution
"""
import asyncio
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.crud.project import project as crud_project
from app.crud.prompt import prompt as crud_prompt
from app.crud.ai_model import ai_model as crud_ai_model
from app.services.execution_service import ExecutionService
from app.schemas.project import ProjectCreate, CompetitorCreate
from app.schemas.prompt import PromptCreate

async def test_complete_flow():
    """Test du workflow complet"""
    db = SessionLocal()
    
    try:
        print("🚀 Test du workflow complet Visibility Tracker")
        print("=" * 50)
        
        # 1. Créer un projet
        print("1. Création d'un projet...")
        project_data = ProjectCreate(
            name="Mon Site E-commerce",
            main_website="https://mon-site.com",
            description="Site e-commerce de test",
            keywords=["casques gaming", "écouteurs bluetooth"],
            competitors=[
                CompetitorCreate(name="Amazon", website="https://amazon.fr")
            ]
        )
        
        project = crud_project.create_with_keywords(db, obj_in=project_data)
        print(f"✅ Projet créé: {project.name} (ID: {project.id})")
        
        # 2. Récupérer un modèle IA
        print("\n2. Récupération d'un modèle IA...")
        ai_models = crud_ai_model.get_active_models(db)
        gpt_model = next((m for m in ai_models if m.provider == "openai"), ai_models[0])
        print(f"✅ Modèle IA: {gpt_model.name} ({gpt_model.provider})")
        
        # 3. Créer un prompt
        print("\n3. Création d'un prompt...")
        prompt_data = PromptCreate(
            project_id=project.id,
            ai_model_id=gpt_model.id,
            name="Test Recommandation Sites",
            template="Recommande-moi 3 sites web fiables pour acheter des {first_keyword}. Je cherche pour le projet {project_name}.",
            description="Test avec vraies APIs",
            tags=["test", "recommandation"],
            is_active=True
        )
        
        prompt = crud_prompt.create_with_tags(db, obj_in=prompt_data)
        print(f"✅ Prompt créé: {prompt.name} (ID: {prompt.id})")
        
        # 4. Exécuter le prompt
        print("\n4. Exécution du prompt avec l'API IA...")
        execution_service = ExecutionService()
        
        result = await execution_service.execute_prompt_analysis(db, prompt.id)
        
        if result.get('success'):
            print("✅ Exécution réussie!")
            print(f"📊 Analyse ID: {result.get('analysis_id')}")
            print(f"🧠 Réponse IA (extrait): {result.get('ai_response', '')[:100]}...")
            print(f"💰 Coût estimé: ${result.get('cost_estimated', 0):.4f}")
            print(f"🔍 Marque mentionnée: {result.get('brand_mentioned', False)}")
            print(f"🌐 Site web mentionné: {result.get('website_mentioned', False)}")
        else:
            print(f"❌ Erreur lors de l'exécution: {result.get('error')}")
            
        print("\n" + "=" * 50)
        print("🎉 Test complet terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_complete_flow()) 
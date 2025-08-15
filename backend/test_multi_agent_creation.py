#!/usr/bin/env python3
"""
Script de test pour la création de prompts multi-agents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.crud.prompt import crud_prompt
from app.crud.project import crud_project
from app.crud.ai_model import crud_ai_model
from app.schemas.prompt import PromptCreate
from sqlalchemy import text

def test_multi_agent_creation():
    """Test de création d'un prompt multi-agents"""
    db = SessionLocal()
    
    try:
        print("🧪 Test de création de prompt multi-agents")
        print("=" * 50)
        
        # 1. Récupérer un projet existant
        projects = crud_project.get_multi(db, limit=1)
        if not projects:
            print("❌ Aucun projet trouvé")
            return
        
        project = projects[0]
        print(f"📁 Projet: {project.name} ({project.id[:8]}...)")
        
        # 2. Récupérer les modèles IA actifs
        all_models = crud_ai_model.get_multi(db)
        ai_models = [model for model in all_models if model.is_active]
        if len(ai_models) < 2:
            print(f"❌ Pas assez de modèles IA actifs ({len(ai_models)} trouvés)")
            return
        
        print(f"🤖 Modèles IA actifs: {len(ai_models)}")
        for model in ai_models[:3]:
            print(f"   - {model.name} ({model.provider})")
        
        # 3. Créer un prompt multi-agents
        selected_models = ai_models[:2]  # Prendre les 2 premiers
        model_ids = [model.id for model in selected_models]
        
        prompt_data = PromptCreate(
            name="Test Multi-Agents Script",
            description="Prompt de test créé via script pour valider le multi-agents",
            template="Analysez {{query}} pour notre marque {{brand}} dans le secteur {{sector}}. Donnez votre avis sur {{topic}}.",
            project_id=project.id,
            is_multi_agent=True,
            ai_model_ids=model_ids,
            tags=["test", "multi-agents", "script"],
            is_active=True
        )
        
        print(f"\n🔧 Création du prompt multi-agents...")
        print(f"   - Nom: {prompt_data.name}")
        print(f"   - Modèles sélectionnés: {[m.name for m in selected_models]}")
        print(f"   - Mode multi-agent: {prompt_data.is_multi_agent}")
        
        # 4. Créer le prompt
        new_prompt = crud_prompt.create_with_tags_and_models(db, obj_in=prompt_data)
        
        print(f"\n✅ Prompt créé avec succès!")
        print(f"   - ID: {new_prompt.id[:8]}...")
        print(f"   - Nom: {new_prompt.name}")
        print(f"   - Multi-agent: {new_prompt.is_multi_agent}")
        
        # 5. Vérifier les relations créées
        full_prompt = crud_prompt.get_with_relations(db, new_prompt.id)
        if full_prompt:
            print(f"   - Relations ai_models: {len(full_prompt.ai_models)}")
            for pam in full_prompt.ai_models:
                model_name = pam.ai_model.name if pam.ai_model else "Inconnu"
                print(f"     * {model_name} (actif: {pam.is_active})")
        
        # 6. Vérifier dans la base de données
        count = db.execute(text("SELECT COUNT(*) FROM prompt_ai_models WHERE prompt_id = :prompt_id"), 
                          {"prompt_id": new_prompt.id}).scalar()
        print(f"   - Entrées en base: {count}")
        
        print(f"\n🎉 Test réussi! Le prompt multi-agents fonctionne correctement.")
        
        return new_prompt.id
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    test_multi_agent_creation() 
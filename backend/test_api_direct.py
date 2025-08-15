#!/usr/bin/env python3
"""
Test direct de l'API IA sans serveur
"""
import asyncio
from app.services.ai_service import AIService
from app.models.ai_model import AIModel
from app.enums import AIProviderEnum

async def test_ai_direct():
    """Test direct du service IA"""
    print("🧪 Test direct du service IA")
    print("=" * 40)
    
    # Créer un modèle IA factice
    ai_model = AIModel(
        name="GPT-3.5 Turbo",
        provider="openai",  # String, pas enum
        model_identifier="gpt-3.5-turbo",
        max_tokens=4096,
        cost_per_1k_tokens=0.0015,
        is_active=True
    )
    
    print(f"Modèle: {ai_model.name}")
    print(f"Fournisseur: {ai_model.provider} (type: {type(ai_model.provider)})")
    print(f"Comparaison: {ai_model.provider} == {AIProviderEnum.OPENAI.value} ? {ai_model.provider == AIProviderEnum.OPENAI.value}")
    
    # Test du service
    ai_service = AIService()
    
    try:
        result = await ai_service.execute_prompt(
            ai_model=ai_model,
            prompt="Dis juste 'Bonjour' pour tester",
            max_tokens=10
        )
        
        if result['success']:
            print("✅ Succès!")
            print(f"Réponse: {result['ai_response']}")
            print(f"Tokens: {result['tokens_used']}")
        else:
            print(f"❌ Erreur: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_direct()) 
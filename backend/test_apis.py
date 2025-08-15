#!/usr/bin/env python3
"""
Script de test simple pour vérifier les APIs IA
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

async def test_openai():
    """Test simple de l'API OpenAI"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY non configurée")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'user', 'content': 'Dis juste "OK" pour tester'}
        ],
        'max_tokens': 5
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"✅ OpenAI: {content}")
                return True
            else:
                print(f"❌ OpenAI erreur {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ OpenAI exception: {e}")
        return False

async def test_google():
    """Test simple de l'API Google Gemini"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY non configurée")
        return False
    
    payload = {
        'contents': [
            {
                'parts': [
                    {'text': 'Dis juste "OK" pour tester'}
                ]
            }
        ],
        'generationConfig': {
            'maxOutputTokens': 5
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}',
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    print(f"✅ Google: {content}")
                    return True
                else:
                    print(f"❌ Google: réponse vide")
                    return False
            else:
                print(f"❌ Google erreur {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Google exception: {e}")
        return False

async def main():
    print("🧪 Test des APIs IA...")
    print("-" * 40)
    
    # Test OpenAI
    await test_openai()
    
    # Test Google
    await test_google()
    
    print("-" * 40)
    print("✨ Tests terminés")

if __name__ == "__main__":
    asyncio.run(main()) 
import asyncio
import httpx
from typing import Dict, Any

from ..core.config import settings


class OpenAIProvider:
    async def execute(self, model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise ValueError("Clé API OpenAI non configurée")
        # Déterminer si on doit privilégier Responses API (modèles modernes)
        prefer_responses = settings.OPENAI_WEB_SEARCH_ENABLED or model_id.startswith(('gpt-5', 'gpt-4.1', 'o4'))

        # Si la recherche web est activée ou modèle moderne, tenter l'endpoint Responses
        if prefer_responses:
            headers = {
                'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
                'Content-Type': 'application/json',
                # Nécéssaire pour activer le preview web-search côté OpenAI
                'OpenAI-Beta': 'web-search-preview=control'
            }
            payload = {
                'model': model_id,
                'input': prompt,
                # Ajouter l'outil de recherche si activé
                'tools': [{ 'type': 'web_search_preview' }] if settings.OPENAI_WEB_SEARCH_ENABLED else [],
                # Forcer l'usage de l'outil avec la forme recommandée par la doc
                'tool_choice': { 'type': 'web_search_preview' } if settings.OPENAI_WEB_SEARCH_ENABLED else 'auto',
                'max_output_tokens': max_tokens,
            }
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post('https://api.openai.com/v1/responses', headers=headers, json=payload)
                data = response.json()
                if response.status_code == 200 and data:
                    # Essayer output_text, sinon explorer output -> content -> text
                    content = data.get('output_text') or ''
                    if not content:
                        try:
                            output = data.get('output') or []
                            texts = []
                            for item in output:
                                # message -> content -> [{ type: 'output_text', text: '...' }]
                                contents = item.get('content') or []
                                for c in contents:
                                    t = c.get('text') or c.get('content')
                                    if isinstance(t, str):
                                        texts.append(t)
                            content = "\n".join(texts).strip()
                        except Exception:
                            content = ''
                    if content:
                        tokens_used = data.get('usage', {}).get('total_tokens', 0)
                        return {
                            'content': content,
                            'tokens_used': tokens_used,
                            'raw_response': data,
                            'web_search_used': True,
                            'actual_model': model_id,
                        }
                # si l'API responses échoue (modèle non supporté), tenter un modèle compatible
                alt_model = 'gpt-4.1'
                try:
                    alt_payload = dict(payload)
                    alt_payload['model'] = alt_model
                    alt_response = await client.post('https://api.openai.com/v1/responses', headers=headers, json=alt_payload)
                    alt_data = alt_response.json()
                    if alt_response.status_code == 200 and alt_data:
                        content = alt_data.get('output_text') or ''
                        if not content:
                            try:
                                output = alt_data.get('output') or []
                                texts = []
                                for item in output:
                                    contents = item.get('content') or []
                                    for c in contents:
                                        t = c.get('text') or c.get('content')
                                        if isinstance(t, str):
                                            texts.append(t)
                                content = "\n".join(texts).strip()
                            except Exception:
                                content = ''
                        if content:
                            return {
                                'content': content,
                                'tokens_used': alt_data.get('usage', {}).get('total_tokens', 0),
                                'raw_response': alt_data,
                                'web_search_used': True,
                                'actual_model': alt_model,
                            }
                except Exception:
                    pass
                # si tout échoue, retomber en chat.completions uniquement pour les modèles chat historiques

        headers = {
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model_id,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.7,
        }
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload)
            data = response.json()
            if response.status_code != 200:
                raise ValueError(f"Erreur OpenAI {response.status_code}: {data}")
            return {
                'content': data['choices'][0]['message']['content'],
                'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                'raw_response': data,
                'web_search_used': False,
                'actual_model': model_id,
            }


class AnthropicProvider:
    async def execute(self, model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Clé API Anthropic non configurée")
        headers = {
            'x-api-key': settings.ANTHROPIC_API_KEY,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
        }
        payload = {
            'model': model_id,
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post('https://api.anthropic.com/v1/messages', headers=headers, json=payload)
            data = response.json()
            if response.status_code != 200:
                raise ValueError(f"Erreur Anthropic {response.status_code}: {data}")
            content = data['content'][0]['text'] if data.get('content') else ''
            tokens_used = (data.get('usage', {}).get('input_tokens', 0) +
                           data.get('usage', {}).get('output_tokens', 0))
            return {
                'content': content,
                'tokens_used': tokens_used,
                'raw_response': data,
            }


class GoogleProvider:
    async def execute(self, model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Clé API Google non configurée")
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={settings.GOOGLE_API_KEY}'
        headers = {'Content-Type': 'application/json'}
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'maxOutputTokens': max_tokens, 'temperature': 0.7},
        }
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            data = response.json()
            if response.status_code != 200:
                raise ValueError(f"Erreur Google {response.status_code}: {data}")
            content = ''
            if 'candidates' in data and data['candidates']:
                if 'content' in data['candidates'][0]:
                    parts = data['candidates'][0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        content = parts[0]['text']
            tokens_used = len(prompt.split()) + len(content.split())
            return {'content': content, 'tokens_used': tokens_used, 'raw_response': data}


class MistralProviderStub:
    async def execute(self, model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        raise NotImplementedError("Fournisseur Mistral non encore implémenté")



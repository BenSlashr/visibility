import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, Protocol
from enum import Enum
from datetime import datetime

from ..core.config import settings
import httpx
from ..models.ai_model import AIModel
from ..enums import AIProviderEnum
from .providers import OpenAIProvider, AnthropicProvider, GoogleProvider, MistralProviderStub

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Exception personnalisée pour les erreurs du service IA"""
    pass

class ProviderStrategy(Protocol):
    async def execute(self, model_id: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        ...


class AIService:
    """
    Service pour les appels aux APIs des modèles IA
    Supporte OpenAI, Anthropic, et autres fournisseurs
    """
    
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = 3
        self.retry_delay = 1  # secondes
        # Stratégies par fournisseur
        self.provider_strategies = {
            AIProviderEnum.OPENAI.value: OpenAIProvider(),
            AIProviderEnum.ANTHROPIC.value: AnthropicProvider(),
            AIProviderEnum.GOOGLE.value: GoogleProvider(),
            AIProviderEnum.MISTRAL.value: MistralProviderStub(),
        }
        
    async def execute_prompt(
        self, 
        ai_model: AIModel, 
        prompt: str, 
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécute un prompt avec le modèle IA spécifié
        
        Args:
            ai_model: Instance du modèle IA à utiliser
            prompt: Texte du prompt à exécuter
            max_tokens: Nombre maximum de tokens (override)
            
        Returns:
            Dict avec la réponse, les métadonnées et les coûts
            
        Raises:
            AIServiceError: En cas d'erreur d'exécution
        """
        start_time = datetime.utcnow()
        
        try:
            # Valider les paramètres
            if not prompt.strip():
                raise AIServiceError("Le prompt ne peut pas être vide")
            
            if not ai_model.is_active:
                raise AIServiceError(f"Le modèle {ai_model.name} n'est pas actif")
            
            # Déterminer le nombre de tokens
            effective_max_tokens = max_tokens or ai_model.max_tokens
            if effective_max_tokens > ai_model.max_tokens:
                logger.warning(f"Max tokens demandé ({effective_max_tokens}) > limite modèle ({ai_model.max_tokens})")
                effective_max_tokens = ai_model.max_tokens
            
            # Appeler via stratégie du fournisseur
            strategy = self.provider_strategies.get(ai_model.provider)
            if not strategy:
                raise AIServiceError(f"Fournisseur non supporté: {ai_model.provider}")
            response_data = await strategy.execute(
                ai_model.model_identifier,
                prompt,
                effective_max_tokens
            )
            
            # Calculer les métriques
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculer le coût estimé
            tokens_used = response_data.get('tokens_used', 0)
            cost_estimated = self._calculate_cost(tokens_used, ai_model.cost_per_1k_tokens)
            
            result = {
                'ai_response': response_data['content'],
                'ai_model_used': ai_model.name,
                'tokens_used': tokens_used,
                'processing_time_ms': processing_time_ms,
                'cost_estimated': cost_estimated,
                'success': True,
                'error': None,
                'raw_response': response_data.get('raw_response', {}),
                'web_search_used': bool(response_data.get('web_search_used', False))
            }
            
            logger.info(f"Prompt exécuté avec succès: {ai_model.name}, {tokens_used} tokens, {processing_time_ms}ms")
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            error_msg = f"Erreur lors de l'exécution du prompt avec {ai_model.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'ai_response': '',
                'ai_model_used': ai_model.name,
                'tokens_used': 0,
                'processing_time_ms': processing_time_ms,
                'cost_estimated': 0.0,
                'success': False,
                'error': error_msg,
                'raw_response': {}
            }
    
    # Anciennes méthodes _call_* supprimées (remplacées par Provider strategies)
    
    def _calculate_cost(self, tokens_used: int, cost_per_1k_tokens: float) -> float:
        """Calcule le coût estimé en USD"""
        if tokens_used <= 0:
            return 0.0
        return (tokens_used / 1000) * cost_per_1k_tokens
    
    async def test_api_key(self, provider: AIProviderEnum) -> Dict[str, Any]:
        """
        Teste la validité d'une clé API
        
        Args:
            provider: Fournisseur à tester
            
        Returns:
            Dict avec le statut du test
        """
        try:
            if provider == AIProviderEnum.OPENAI:
                if not settings.OPENAI_API_KEY:
                    return {'valid': False, 'error': 'Clé API non configurée'}
                
                # Test simple avec un prompt court
                headers = {
                    'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [{'role': 'user', 'content': 'Test'}],
                    'max_tokens': 5
                }
                
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        'https://api.openai.com/v1/chat/completions',
                        headers=headers,
                        json=payload
                    )
                    
                    return {
                        'valid': response.status_code == 200,
                        'error': None if response.status_code == 200 else f"Status {response.status_code}"
                    }
            
            elif provider == AIProviderEnum.ANTHROPIC:
                if not settings.ANTHROPIC_API_KEY:
                    return {'valid': False, 'error': 'Clé API non configurée'}
                
                # Test simple avec un prompt court
                headers = {
                    'x-api-key': settings.ANTHROPIC_API_KEY,
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 5,
                    'messages': [{'role': 'user', 'content': 'Test'}]
                }
                
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        'https://api.anthropic.com/v1/messages',
                        headers=headers,
                        json=payload
                    )
                    
                    return {
                        'valid': response.status_code == 200,
                        'error': None if response.status_code == 200 else f"Status {response.status_code}"
                    }
            
            elif provider == AIProviderEnum.GOOGLE:
                if not settings.GOOGLE_API_KEY:
                    return {'valid': False, 'error': 'Clé API non configurée'}
                
                # Test simple avec un prompt court
                payload = {
                    'contents': [
                        {
                            'parts': [
                                {'text': 'Test'}
                            ]
                        }
                    ],
                    'generationConfig': {
                        'maxOutputTokens': 5
                    }
                }
                
                url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GOOGLE_API_KEY}'
                
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(url, json=payload)
                    
                    return {
                        'valid': response.status_code == 200,
                        'error': None if response.status_code == 200 else f"Status {response.status_code}"
                    }
            
            else:
                return {'valid': False, 'error': f'Fournisseur non supporté: {provider}'}
                
        except Exception as e:
            return {'valid': False, 'error': str(e)}

# Instance globale du service
ai_service = AIService() 
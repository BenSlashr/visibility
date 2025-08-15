"""
Énumérations utilisées dans l'application
"""
from enum import Enum

class AIProviderEnum(str, Enum):
    """Fournisseurs d'API IA supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral" 
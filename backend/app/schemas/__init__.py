# Schémas Pydantic pour la validation et sérialisation des données

# Import des schémas de base
from .base import BaseSchema, TimestampSchema, BaseCreateSchema, BaseUpdateSchema, BaseReadSchema

# Import des schémas par domaine
from .project import (
    ProjectCreate, ProjectUpdate, ProjectRead, ProjectSummary,
    CompetitorCreate, CompetitorUpdate, CompetitorRead,
    KeywordCreate, KeywordRead
)

from .ai_model import (
    AIProviderEnum, AIModelCreate, AIModelUpdate, AIModelRead, AIModelSummary
)

from .prompt import (
    PromptCreate, PromptUpdate, PromptRead, PromptSummary,
    PromptAIModelCreate, PromptAIModelRead,
    PromptExecuteRequest, PromptExecuteResponse
)

from .analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisRead, AnalysisSummary,
    AnalysisCompetitorCreate, AnalysisCompetitorRead,
    AnalysisStats, ProjectAnalysisStats, CompetitorAnalysisStats
)

# Export pour faciliter les imports
__all__ = [
    # Base
    'BaseSchema', 'TimestampSchema', 'BaseCreateSchema', 'BaseUpdateSchema', 'BaseReadSchema',
    
    # Project
    'ProjectCreate', 'ProjectUpdate', 'ProjectRead', 'ProjectSummary',
    'CompetitorCreate', 'CompetitorUpdate', 'CompetitorRead',
    'KeywordCreate', 'KeywordRead',
    
    # AI Model
    'AIProviderEnum', 'AIModelCreate', 'AIModelUpdate', 'AIModelRead', 'AIModelSummary',
    
    # Prompt
    'PromptCreate', 'PromptUpdate', 'PromptRead', 'PromptSummary',
    'PromptTagCreate', 'PromptTagRead',
    'PromptExecuteRequest', 'PromptExecuteResponse',
    
    # Analysis
    'AnalysisCreate', 'AnalysisUpdate', 'AnalysisRead', 'AnalysisSummary',
    'AnalysisCompetitorCreate', 'AnalysisCompetitorRead',
    'AnalysisStats', 'ProjectAnalysisStats', 'CompetitorAnalysisStats'
] 
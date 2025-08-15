# Modèles de données SQLAlchemy

# Import de la base
from .base import Base, BaseModel, TimestampMixin, generate_uuid

# Import de tous les modèles
from .project import Project, ProjectKeyword, Competitor
from .ai_model import AIModel
from .prompt import Prompt, PromptTag, PromptAIModel
from .analysis import Analysis, AnalysisCompetitor
from .analysis_source import AnalysisSource
from .analysis_topics import AnalysisTopics
from .app_setting import AppSetting
from .serp import SERPImport, SERPKeyword, PromptSERPAssociation

# Export pour faciliter les imports
__all__ = [
    'Base',
    'BaseModel', 
    'TimestampMixin',
    'generate_uuid',
    'Project',
    'ProjectKeyword',
    'Competitor',
    'AIModel',
    'Prompt',
    'PromptTag',
    'PromptAIModel',
    'Analysis',
    'AnalysisCompetitor',
    'AnalysisSource',
    'AnalysisTopics',
    'AppSetting',
    'SERPImport',
    'SERPKeyword',
    'PromptSERPAssociation'
] 
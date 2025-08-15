# Opérations CRUD (Create, Read, Update, Delete) pour la base de données

from .base import CRUDBase
from .project import crud_project
from .ai_model import crud_ai_model
from .prompt import crud_prompt
from .analysis import crud_analysis
from .analysis_source import crud_analysis_source
from .serp import crud_serp_import, crud_serp_keyword, crud_prompt_serp_association

# Export pour faciliter les imports
__all__ = [
    'CRUDBase',
    'crud_project',
    'crud_ai_model',
    'crud_prompt', 
    'crud_analysis',
    'crud_analysis_source',
    'crud_serp_import',
    'crud_serp_keyword',
    'crud_prompt_serp_association'
] 
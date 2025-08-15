from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from datetime import datetime

from .base import CRUDBase
from ..models.prompt import Prompt, PromptTag, PromptAIModel
from ..schemas.prompt import PromptCreate, PromptUpdate

class CRUDPrompt(CRUDBase[Prompt, PromptCreate, PromptUpdate]):
    def create_with_tags_and_models(self, db: Session, *, obj_in: PromptCreate) -> Prompt:
        """Crée un prompt avec ses tags et modèles IA (multi-agents ou unique)"""
        # Créer le prompt principal
        prompt_data = obj_in.dict(exclude={'tags', 'ai_model_ids'})
        db_prompt = Prompt(**prompt_data)
        db.add(db_prompt)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les tags
        for tag_name in obj_in.tags:
            db_tag = PromptTag(
                prompt_id=db_prompt.id,
                tag_name=tag_name
            )
            db.add(db_tag)
        
        # Gérer les modèles IA selon le mode
        if obj_in.is_multi_agent:
            # Mode multi-agents : utiliser ai_model_ids
            for ai_model_id in obj_in.ai_model_ids:
                db_prompt_model = PromptAIModel(
                    prompt_id=db_prompt.id,
                    ai_model_id=ai_model_id,
                    is_active=True
                )
                db.add(db_prompt_model)
        else:
            # Mode unique : utiliser ai_model_id et créer une relation dans prompt_ai_models
            if obj_in.ai_model_id:
                db_prompt_model = PromptAIModel(
                    prompt_id=db_prompt.id,
                    ai_model_id=obj_in.ai_model_id,
                    is_active=True
                )
                db.add(db_prompt_model)
        
        db.commit()
        db.refresh(db_prompt)
        return db_prompt
    
    def create_with_tags(self, db: Session, *, obj_in: PromptCreate) -> Prompt:
        """Alias pour compatibilité ascendante"""
        return self.create_with_tags_and_models(db, obj_in=obj_in)
    
    def get_with_relations(self, db: Session, id: str) -> Optional[Prompt]:
        """Récupère un prompt avec toutes ses relations"""
        return db.query(Prompt).options(
            joinedload(Prompt.tags),
            joinedload(Prompt.ai_model),
            joinedload(Prompt.ai_models).joinedload(PromptAIModel.ai_model),  # Multi-agents
            joinedload(Prompt.project),
            joinedload(Prompt.analyses)
        ).filter(Prompt.id == id).first()
    
    def get_by_project(self, db: Session, project_id: str, *, skip: int = 0, limit: int = 100) -> List[Prompt]:
        """Récupère les prompts d'un projet"""
        return db.query(Prompt).filter(
            Prompt.project_id == project_id
        ).offset(skip).limit(limit).all()

    def get_by_project_and_name(self, db: Session, project_id: str, name: str) -> Optional[Prompt]:
        """Récupère un prompt par (projet, nom)"""
        return db.query(Prompt).filter(
            Prompt.project_id == project_id,
            Prompt.name == name
        ).first()
    
    def get_active_by_project(self, db: Session, project_id: str) -> List[Prompt]:
        """Récupère les prompts actifs d'un projet"""
        return db.query(Prompt).filter(
            Prompt.project_id == project_id,
            Prompt.is_active == True
        ).all()
    
    def update_models(self, db: Session, *, prompt_id: str, ai_model_ids: List[str], is_multi_agent: bool = False) -> Prompt:
        """Met à jour les modèles IA associés à un prompt"""
        prompt = self.get_or_404(db, prompt_id)
        
        # Supprimer les anciennes relations
        db.query(PromptAIModel).filter(PromptAIModel.prompt_id == prompt_id).delete()
        
        # Mettre à jour le mode multi-agent
        prompt.is_multi_agent = is_multi_agent
        
        # Ajouter les nouvelles relations
        for ai_model_id in ai_model_ids:
            db_prompt_model = PromptAIModel(
                prompt_id=prompt_id,
                ai_model_id=ai_model_id,
                is_active=True
            )
            db.add(db_prompt_model)
        
        # Mettre à jour ai_model_id pour compatibilité
        if not is_multi_agent and ai_model_ids:
            prompt.ai_model_id = ai_model_ids[0]
        else:
            prompt.ai_model_id = None
        
        db.commit()
        db.refresh(prompt)
        return prompt
    
    def toggle_model_active(self, db: Session, *, prompt_id: str, ai_model_id: str, is_active: bool) -> bool:
        """Active/désactive un modèle IA spécifique pour un prompt multi-agents"""
        relation = db.query(PromptAIModel).filter(
            PromptAIModel.prompt_id == prompt_id,
            PromptAIModel.ai_model_id == ai_model_id
        ).first()
        
        if not relation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relation prompt-modèle non trouvée"
            )
        
        relation.is_active = is_active
        db.commit()
        return True
    
    def get_multi_agent_prompts(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Prompt]:
        """Récupère tous les prompts multi-agents"""
        return db.query(Prompt).filter(
            Prompt.is_multi_agent == True
        ).offset(skip).limit(limit).all()
    
    def get_prompts_by_model(self, db: Session, ai_model_id: str, *, skip: int = 0, limit: int = 100) -> List[Prompt]:
        """Récupère tous les prompts utilisant un modèle IA spécifique"""
        return db.query(Prompt).join(PromptAIModel).filter(
            PromptAIModel.ai_model_id == ai_model_id,
            PromptAIModel.is_active == True
        ).offset(skip).limit(limit).all()
    
    def increment_execution_count(self, db: Session, *, prompt_id: str) -> bool:
        """Incrémente le compteur d'exécution d'un prompt"""
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if prompt:
            prompt.execution_count = (prompt.execution_count or 0) + 1
            prompt.last_executed_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    def get_execution_stats(self, db: Session, prompt_id: str) -> dict:
        """Récupère les statistiques d'exécution d'un prompt"""
        prompt = self.get_with_relations(db, prompt_id)
        if not prompt:
            return {}
        
        # Statistiques de base
        stats = {
            'prompt_id': prompt.id,
            'prompt_name': prompt.name,
            'execution_count': prompt.execution_count or 0,
            'last_executed_at': prompt.last_executed_at,
            'is_multi_agent': prompt.is_multi_agent,
            'total_analyses': len(prompt.analyses),
            'active_models': len(prompt.active_ai_models)
        }
        
        # Statistiques par modèle pour les multi-agents
        if prompt.is_multi_agent:
            model_stats = {}
            for analysis in prompt.analyses:
                model_name = analysis.ai_model_used
                if model_name not in model_stats:
                    model_stats[model_name] = {
                        'count': 0,
                        'avg_visibility': 0,
                        'total_cost': 0,
                        'total_tokens': 0
                    }
                
                model_stats[model_name]['count'] += 1
                model_stats[model_name]['avg_visibility'] += analysis.visibility_score
                model_stats[model_name]['total_cost'] += analysis.cost_estimated
                model_stats[model_name]['total_tokens'] += analysis.tokens_used
            
            # Calculer les moyennes
            for model_name, data in model_stats.items():
                if data['count'] > 0:
                    data['avg_visibility'] = data['avg_visibility'] / data['count']
            
            stats['model_stats'] = model_stats
        
        return stats

# Instance globale du CRUD
crud_prompt = CRUDPrompt(Prompt) 
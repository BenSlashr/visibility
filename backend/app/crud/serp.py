from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from ..crud.base import CRUDBase
from ..models.serp import SERPImport, SERPKeyword, PromptSERPAssociation
from ..schemas.serp import (
    SERPImportCreate,
    SERPKeywordCreate, SERPKeywordUpdate, 
    PromptSERPAssociationCreate, PromptSERPAssociationUpdate
)

class CRUDSERPImport(CRUDBase[SERPImport, SERPImportCreate, Dict[str, Any]]):
    """CRUD operations pour les imports SERP"""
    
    def get_active_by_project(self, db: Session, *, project_id: str) -> Optional[SERPImport]:
        """Récupère l'import SERP actif d'un projet"""
        return db.query(SERPImport).filter(
            and_(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            )
        ).first()
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[SERPImport]:
        """Récupère tous les imports d'un projet (historique)"""
        return db.query(SERPImport).filter(
            SERPImport.project_id == project_id
        ).order_by(desc(SERPImport.import_date)).offset(skip).limit(limit).all()
    
    def deactivate_previous_imports(self, db: Session, *, project_id: str) -> int:
        """Désactive tous les imports précédents d'un projet"""
        updated_count = db.query(SERPImport).filter(
            and_(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            )
        ).update({"is_active": False})
        return updated_count
    
    def create_with_deactivation(self, db: Session, *, obj_in: SERPImportCreate) -> SERPImport:
        """Crée un nouvel import en désactivant les précédents"""
        # Désactiver imports précédents
        self.deactivate_previous_imports(db, project_id=obj_in.project_id)
        
        # Créer le nouvel import
        return super().create(db, obj_in=obj_in)


class CRUDSERPKeyword(CRUDBase[SERPKeyword, SERPKeywordCreate, SERPKeywordUpdate]):
    """CRUD operations pour les mots-clés SERP"""
    
    def get_by_import(self, db: Session, *, import_id: str, skip: int = 0, limit: int = 1000) -> List[SERPKeyword]:
        """Récupère tous les mots-clés d'un import"""
        return db.query(SERPKeyword).filter(
            SERPKeyword.import_id == import_id
        ).order_by(asc(SERPKeyword.position)).offset(skip).limit(limit).all()
    
    def get_by_project(self, db: Session, *, project_id: str, active_only: bool = True) -> List[SERPKeyword]:
        """Récupère les mots-clés SERP d'un projet"""
        query = db.query(SERPKeyword).filter(SERPKeyword.project_id == project_id)
        
        if active_only:
            # Jointure avec import actif
            query = query.join(SERPImport).filter(SERPImport.is_active == True)
        
        return query.order_by(asc(SERPKeyword.position)).all()
    
    def search_by_keyword(self, db: Session, *, project_id: str, search_term: str, limit: int = 20) -> List[SERPKeyword]:
        """Recherche des mots-clés par terme de recherche"""
        return db.query(SERPKeyword).join(SERPImport).filter(
            and_(
                SERPKeyword.project_id == project_id,
                SERPImport.is_active == True,
                SERPKeyword.keyword_normalized.ilike(f"%{search_term}%")
            )
        ).order_by(asc(SERPKeyword.position)).limit(limit).all()
    
    def get_top_keywords(self, db: Session, *, project_id: str, position_limit: int = 10, limit: int = 50) -> List[SERPKeyword]:
        """Récupère les mots-clés les mieux positionnés"""
        return db.query(SERPKeyword).join(SERPImport).filter(
            and_(
                SERPKeyword.project_id == project_id,
                SERPImport.is_active == True,
                SERPKeyword.position <= position_limit
            )
        ).order_by(asc(SERPKeyword.position)).limit(limit).all()
    
    def bulk_create(self, db: Session, *, obj_in_list: List[SERPKeywordCreate]) -> List[SERPKeyword]:
        """Création en masse de mots-clés SERP"""
        db_objs = [SERPKeyword(**obj_in.dict()) for obj_in in obj_in_list]
        db.add_all(db_objs)
        db.flush()  # Pour obtenir les IDs
        return db_objs


class CRUDPromptSERPAssociation(CRUDBase[PromptSERPAssociation, PromptSERPAssociationCreate, PromptSERPAssociationUpdate]):
    """CRUD operations pour les associations prompt-SERP"""
    
    def get_by_prompt(self, db: Session, *, prompt_id: str) -> Optional[PromptSERPAssociation]:
        """Récupère l'association d'un prompt"""
        return db.query(PromptSERPAssociation).filter(
            PromptSERPAssociation.prompt_id == prompt_id
        ).first()
    
    def get_by_project(self, db: Session, *, project_id: str) -> List[PromptSERPAssociation]:
        """Récupère toutes les associations d'un projet"""
        return db.query(PromptSERPAssociation).join(SERPKeyword).filter(
            SERPKeyword.project_id == project_id
        ).all()
    
    def get_by_type(self, db: Session, *, project_id: str, association_type: str) -> List[PromptSERPAssociation]:
        """Récupère les associations par type (manual, auto, suggested)"""
        return db.query(PromptSERPAssociation).join(SERPKeyword).filter(
            and_(
                SERPKeyword.project_id == project_id,
                PromptSERPAssociation.association_type == association_type
            )
        ).all()
    
    def set_association(self, db: Session, *, prompt_id: str, serp_keyword_id: Optional[str], association_type: str = "manual") -> Optional[PromptSERPAssociation]:
        """Définit l'association d'un prompt (supprime l'ancienne si elle existe)"""
        # Supprimer association existante
        db.query(PromptSERPAssociation).filter(
            PromptSERPAssociation.prompt_id == prompt_id
        ).delete()
        
        # Créer nouvelle association si keyword fourni
        if serp_keyword_id:
            obj_in = PromptSERPAssociationCreate(
                prompt_id=prompt_id,
                serp_keyword_id=serp_keyword_id,
                association_type=association_type
            )
            return super().create(db, obj_in=obj_in)
        
        return None
    
    def bulk_create_associations(self, db: Session, *, associations: List[PromptSERPAssociationCreate]) -> List[PromptSERPAssociation]:
        """Création en masse d'associations"""
        db_objs = [PromptSERPAssociation(**assoc.dict()) for assoc in associations]
        db.add_all(db_objs)
        db.flush()
        return db_objs
    
    def clear_auto_associations_for_project(self, db: Session, *, project_id: str) -> int:
        """Supprime toutes les associations automatiques d'un projet"""
        deleted_count = db.query(PromptSERPAssociation).join(SERPKeyword).filter(
            and_(
                SERPKeyword.project_id == project_id,
                PromptSERPAssociation.association_type == 'auto'
            )
        ).delete(synchronize_session=False)
        return deleted_count
    
    def get_unassociated_prompts(self, db: Session, *, project_id: str) -> List[str]:
        """Récupère les IDs des prompts sans association SERP"""
        from ..models.prompt import Prompt
        
        # Sous-requête des prompts avec association
        associated_prompts = db.query(PromptSERPAssociation.prompt_id).join(SERPKeyword).filter(
            SERPKeyword.project_id == project_id
        ).subquery()
        
        # Prompts du projet sans association
        unassociated = db.query(Prompt.id).filter(
            and_(
                Prompt.project_id == project_id,
                ~Prompt.id.in_(associated_prompts)
            )
        ).all()
        
        return [prompt_id[0] for prompt_id in unassociated]
    
    def get_association_stats(self, db: Session, *, project_id: str) -> Dict[str, Any]:
        """Récupère les statistiques d'association pour un projet"""
        from ..models.prompt import Prompt
        
        # Total prompts du projet
        total_prompts = db.query(Prompt).filter(Prompt.project_id == project_id).count()
        
        # Associations par type
        auto_count = self.get_by_type(db, project_id=project_id, association_type='auto').__len__()
        manual_count = self.get_by_type(db, project_id=project_id, association_type='manual').__len__()
        suggested_count = self.get_by_type(db, project_id=project_id, association_type='suggested').__len__()
        
        total_associated = auto_count + manual_count + suggested_count
        unassociated_count = total_prompts - total_associated
        
        return {
            'total_prompts': total_prompts,
            'auto_associations': auto_count,
            'manual_associations': manual_count,
            'suggested_associations': suggested_count,
            'unassociated_prompts': unassociated_count,
            'association_rate': round((total_associated / total_prompts * 100), 1) if total_prompts > 0 else 0
        }


# Instances globales des CRUD
crud_serp_import = CRUDSERPImport(SERPImport)
crud_serp_keyword = CRUDSERPKeyword(SERPKeyword)
crud_prompt_serp_association = CRUDPromptSERPAssociation(PromptSERPAssociation)
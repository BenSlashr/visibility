from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from .base import CRUDBase
from ..models.project import Project, ProjectKeyword, Competitor
from ..schemas.project import ProjectCreate, ProjectUpdate, CompetitorCreate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    def create_with_keywords(self, db: Session, *, obj_in: ProjectCreate) -> Project:
        """Crée un projet avec ses mots-clés"""
        # Créer le projet principal
        project_data = obj_in.dict(exclude={'keywords'})
        db_project = Project(**project_data)
        db.add(db_project)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les mots-clés
        for keyword in obj_in.keywords:
            db_keyword = ProjectKeyword(
                project_id=db_project.id,
                keyword=keyword
            )
            db.add(db_keyword)
        
        db.commit()
        db.refresh(db_project)
        return db_project
    
    def get_with_relations(self, db: Session, id: str) -> Optional[Project]:
        """Récupère un projet avec toutes ses relations"""
        return db.query(Project).options(
            joinedload(Project.keywords),
            joinedload(Project.competitors),
            joinedload(Project.prompts),
            joinedload(Project.analyses)
        ).filter(Project.id == id).first()
    
    def get_multi_with_stats(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Récupère les projets avec statistiques de base"""
        return db.query(Project).options(
            joinedload(Project.keywords),
            joinedload(Project.competitors)
        ).offset(skip).limit(limit).all()
    
    def update_keywords(self, db: Session, *, project_id: str, keywords: List[str]) -> Project:
        """Met à jour les mots-clés d'un projet"""
        project = self.get_or_404(db, project_id)
        
        # Supprimer les anciens mots-clés
        db.query(ProjectKeyword).filter(ProjectKeyword.project_id == project_id).delete()
        
        # Ajouter les nouveaux
        for keyword in keywords:
            db_keyword = ProjectKeyword(
                project_id=project_id,
                keyword=keyword
            )
            db.add(db_keyword)
        
        db.commit()
        db.refresh(project)
        return project
    
    def add_competitor(self, db: Session, *, project_id: str, competitor_in: CompetitorCreate) -> Competitor:
        """Ajoute un concurrent à un projet"""
        # Vérifier que le projet existe
        project = self.get_or_404(db, project_id)
        
        # Vérifier que le concurrent n'existe pas déjà
        existing = db.query(Competitor).filter(
            Competitor.project_id == project_id,
            Competitor.website == competitor_in.website
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce concurrent existe déjà pour ce projet"
            )
        
        competitor_data = competitor_in.dict()
        competitor_data['project_id'] = project_id
        db_competitor = Competitor(**competitor_data)
        db.add(db_competitor)
        db.commit()
        db.refresh(db_competitor)
        return db_competitor
    
    def remove_competitor(self, db: Session, *, project_id: str, competitor_id: str) -> bool:
        """Supprime un concurrent d'un projet"""
        competitor = db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.project_id == project_id
        ).first()
        
        if not competitor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concurrent non trouvé"
            )
        
        db.delete(competitor)
        db.commit()
        return True
    
    def get_by_name(self, db: Session, name: str) -> Optional[Project]:
        """Récupère un projet par nom"""
        return db.query(Project).filter(Project.name == name).first()
    
    def search_by_keyword(self, db: Session, keyword: str) -> List[Project]:
        """Recherche des projets par mot-clé"""
        return db.query(Project).join(ProjectKeyword).filter(
            ProjectKeyword.keyword.contains(keyword)
        ).distinct().all()

# Instance globale
crud_project = CRUDProject(Project) 
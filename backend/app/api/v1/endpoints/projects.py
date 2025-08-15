from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_database_session
from app.crud.project import crud_project
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectRead, ProjectSummary,
    CompetitorCreate, CompetitorRead
)

router = APIRouter()

@router.get("/", response_model=List[ProjectSummary])
def get_projects(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    search: Optional[str] = Query(None, description="Recherche par nom ou mot-clé"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des projets avec pagination et recherche
    
    - **skip**: nombre d'éléments à ignorer (pagination)
    - **limit**: nombre maximum d'éléments à retourner
    - **search**: recherche par nom de projet ou mot-clé
    """
    if search:
        projects = crud_project.search_by_keyword(db, search)
        # Appliquer pagination manuelle pour la recherche
        projects = projects[skip:skip + limit]
    else:
        projects = crud_project.get_multi_with_stats(db, skip=skip, limit=limit)
    
    # Enrichir avec les statistiques
    result = []
    for project in projects:
        project_summary = ProjectSummary(
            id=project.id,
            name=project.name,
            main_website=project.main_website,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            keywords_count=len(project.keywords),
            competitors_count=len(project.competitors),
            analyses_count=len(project.analyses) if hasattr(project, 'analyses') else 0
        )
        result.append(project_summary)
    
    return result

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_database_session)
):
    """
    Crée un nouveau projet avec ses mots-clés
    
    - **name**: nom du projet (obligatoire)
    - **main_website**: site web principal (optionnel)
    - **description**: description du projet (optionnel)
    - **keywords**: liste des mots-clés cibles
    """
    # Vérifier que le nom n'existe pas déjà
    existing_project = crud_project.get_by_name(db, project_in.name)
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un projet avec ce nom existe déjà"
        )
    
    project = crud_project.create_with_keywords(db, obj_in=project_in)
    return crud_project.get_with_relations(db, project.id)

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Récupère un projet par ID avec toutes ses relations
    """
    project = crud_project.get_with_relations(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    return project

@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_database_session)
):
    """
    Met à jour un projet
    
    Les mots-clés sont mis à jour séparément via l'endpoint dédié
    """
    project = crud_project.get_or_404(db, project_id)
    
    # Vérifier l'unicité du nom si changé
    if project_in.name and project_in.name != project.name:
        existing = crud_project.get_by_name(db, project_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un projet avec ce nom existe déjà"
            )
    
    project = crud_project.update(db, db_obj=project, obj_in=project_in)
    return crud_project.get_with_relations(db, project.id)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Supprime un projet et toutes ses données associées
    
    ⚠️ Cette action est irréversible et supprime :
    - Le projet
    - Tous ses mots-clés
    - Tous ses concurrents
    - Tous ses prompts
    - Toutes ses analyses
    """
    project = crud_project.get_or_404(db, project_id)
    crud_project.remove(db, id=project_id)

# Endpoints pour les mots-clés
@router.put("/{project_id}/keywords", response_model=ProjectRead)
def update_project_keywords(
    project_id: str,
    keywords: List[str],
    db: Session = Depends(get_database_session)
):
    """
    Met à jour les mots-clés d'un projet
    
    Remplace complètement la liste existante
    """
    project = crud_project.update_keywords(db, project_id=project_id, keywords=keywords)
    return crud_project.get_with_relations(db, project.id)

# Endpoints pour les concurrents
@router.get("/{project_id}/competitors", response_model=List[CompetitorRead])
def get_project_competitors(
    project_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des concurrents d'un projet
    """
    project = crud_project.get_or_404(db, project_id)
    return project.competitors

@router.post("/{project_id}/competitors", response_model=CompetitorRead, status_code=status.HTTP_201_CREATED)
def add_project_competitor(
    project_id: str,
    competitor_in: CompetitorCreate,
    db: Session = Depends(get_database_session)
):
    """
    Ajoute un concurrent à un projet
    
    - **name**: nom du concurrent
    - **website**: site web du concurrent (doit être unique par projet)
    """
    competitor = crud_project.add_competitor(db, project_id=project_id, competitor_in=competitor_in)
    return competitor

@router.delete("/{project_id}/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_competitor(
    project_id: str,
    competitor_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Supprime un concurrent d'un projet
    """
    crud_project.remove_competitor(db, project_id=project_id, competitor_id=competitor_id)

@router.get("/search/{keyword}", response_model=List[ProjectSummary])
def search_projects_by_keyword(
    keyword: str,
    db: Session = Depends(get_database_session)
):
    """
    Recherche des projets par mot-clé
    
    Recherche dans les mots-clés associés aux projets
    """
    projects = crud_project.search_by_keyword(db, keyword)
    
    result = []
    for project in projects:
        project_summary = ProjectSummary(
            id=project.id,
            name=project.name,
            main_website=project.main_website,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            keywords_count=len(project.keywords),
            competitors_count=len(project.competitors),
            analyses_count=len(project.analyses) if hasattr(project, 'analyses') else 0
        )
        result.append(project_summary)
    
    return result 
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ....core.database import get_db
from ....services.serp_service import serp_service, SERPServiceError
from ....models.serp import SERPImport, SERPKeyword, PromptSERPAssociation
from ....models.prompt import Prompt

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/projects/{project_id}/serp/import", response_model=Dict[str, Any])
def import_serp_csv(
    project_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Importe un CSV de positionnement SERP
    Format attendu: keyword,volume,position,url
    """
    try:
        # Vérifier le format de fichier
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")
        
        # Lire le contenu
        content = file.file.read()
        csv_content = content.decode('utf-8')
        
        # Importer
        result = serp_service.import_csv(
            db=db,
            project_id=project_id,
            csv_content=csv_content,
            filename=file.filename,
            notes=notes
        )
        
        return result
        
    except SERPServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/projects/{project_id}/serp/auto-match", response_model=Dict[str, Any])
def auto_match_prompts_keywords(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Associe automatiquement les prompts aux mots-clés SERP"""
    try:
        result = serp_service.auto_match_prompts_to_keywords(db, project_id)
        return result
        
    except SERPServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.put("/prompts/{prompt_id}/serp/association")
def set_prompt_serp_association(
    prompt_id: str,
    association_data: dict,
    db: Session = Depends(get_db)
):
    """Définit manuellement l'association entre un prompt et un mot-clé SERP"""
    try:
        serp_keyword_id = association_data.get('serp_keyword_id')
        result = serp_service.set_manual_association(db, prompt_id, serp_keyword_id)
        return result
        
    except SERPServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/projects/{project_id}/serp/summary", response_model=Dict[str, Any])
def get_project_serp_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Récupère le résumé des données SERP d'un projet"""
    try:
        result = serp_service.get_project_serp_summary(db, project_id)
        return result
        
    except SERPServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/projects/{project_id}/serp/keywords", response_model=Dict[str, Any])
def get_project_serp_keywords(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Récupère la liste des mots-clés SERP d'un projet"""
    try:
        # Import actif
        serp_import = db.query(SERPImport).filter(
            SERPImport.project_id == project_id,
            SERPImport.is_active == True
        ).first()
        
        if not serp_import:
            return {'keywords': []}
        
        keywords = db.query(SERPKeyword).filter(
            SERPKeyword.import_id == serp_import.id
        ).order_by(SERPKeyword.position).all()
        
        return {
            'keywords': [
                {
                    'id': k.id,
                    'keyword': k.keyword,
                    'position': k.position,
                    'volume': k.volume,
                    'url': k.url
                }
                for k in keywords
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/prompts/{prompt_id}/serp/association", response_model=Dict[str, Any])
def get_prompt_serp_association(
    prompt_id: str,
    db: Session = Depends(get_db)
):
    """Récupère l'association SERP d'un prompt"""
    try:
        association = db.query(PromptSERPAssociation).filter(
            PromptSERPAssociation.prompt_id == prompt_id
        ).first()
        
        if not association:
            return {'has_association': False}
        
        serp_keyword = db.query(SERPKeyword).filter(
            SERPKeyword.id == association.serp_keyword_id
        ).first()
        
        return {
            'has_association': True,
            'association': {
                'keyword_id': serp_keyword.id,
                'keyword': serp_keyword.keyword,
                'position': serp_keyword.position,
                'volume': serp_keyword.volume,
                'association_type': association.association_type,
                'matching_score': association.matching_score
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/projects/{project_id}/serp/suggestions", response_model=Dict[str, Any])
async def get_matching_suggestions(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Récupère les suggestions de matching pour les prompts non associés"""
    try:
        result = await serp_service.get_matching_suggestions(project_id, db)
        return result
        
    except SERPServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/projects/{project_id}/serp/associations", response_model=Dict[str, Any])
def get_project_serp_associations(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Récupère toutes les associations SERP d'un projet"""
    try:
        # Récupérer toutes les associations de base
        associations_query = db.query(
            PromptSERPAssociation.prompt_id,
            PromptSERPAssociation.association_type,
            PromptSERPAssociation.matching_score,
            Prompt.name.label('prompt_name'),
            SERPKeyword.keyword,
            SERPKeyword.position.label('serp_position'),
            SERPKeyword.volume,
            SERPKeyword.url
        ).join(
            Prompt, PromptSERPAssociation.prompt_id == Prompt.id
        ).join(
            SERPKeyword, PromptSERPAssociation.serp_keyword_id == SERPKeyword.id
        ).filter(
            Prompt.project_id == project_id
        ).order_by(SERPKeyword.position)
        
        associations = associations_query.all()
        
        # TODO: Debug - Commencer simple puis ajouter les vraies métriques
        visibility_metrics = {}
        
        try:
            # Test simple d'abord
            from datetime import datetime, timedelta
            from ....models.analysis import Analysis
            
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            prompt_ids = [a.prompt_id for a in associations]
            
            print(f"🔍 DEBUG: project_id={project_id}, prompt_ids={prompt_ids[:3]}..." if len(prompt_ids) > 3 else f"🔍 DEBUG: project_id={project_id}, prompt_ids={prompt_ids}")
            
            if prompt_ids:
                # Compter le total d'analyses récentes
                total_analyses_count = db.query(Analysis).filter(
                    Analysis.project_id == project_id,
                    Analysis.created_at >= thirty_days_ago
                ).count()
                
                print(f"📊 DEBUG: total_analyses_count dans les 30 derniers jours = {total_analyses_count}")
                
                # Récupérer les analyses pour les prompts associés
                analyses = db.query(Analysis).filter(
                    Analysis.prompt_id.in_(prompt_ids),
                    Analysis.project_id == project_id,
                    Analysis.created_at >= thirty_days_ago
                ).all()
                
                print(f"🎯 DEBUG: {len(analyses)} analyses trouvées pour les prompts associés")
                
                # Calculer les vraies métriques par prompt
                for prompt_id in set(prompt_ids):
                    prompt_analyses = [a for a in analyses if a.prompt_id == prompt_id]
                    
                    if prompt_analyses:
                        # Calculer les vraies métriques
                        visibility_scores = [a.visibility_score or 0 for a in prompt_analyses]
                        links_count = [1 if a.website_linked else 0 for a in prompt_analyses]
                        positions = [a.ranking_position for a in prompt_analyses if a.ranking_position]
                        
                        visibility_metrics[prompt_id] = {
                            'ai_visibility_percentage': round(sum(visibility_scores) / len(visibility_scores), 2) if visibility_scores else 0,
                            'ai_links_percentage': round((sum(links_count) / len(links_count)) * 100, 2) if links_count else 0,
                            'ai_average_position': round(sum(positions) / len(positions), 2) if positions else None
                        }
                        
                        print(f"📈 Prompt {prompt_id[:8]}: {len(prompt_analyses)} analyses, visibilité={visibility_metrics[prompt_id]['ai_visibility_percentage']:.1f}%, liens={visibility_metrics[prompt_id]['ai_links_percentage']:.1f}%")
                    else:
                        # Pas d'analyses récentes pour ce prompt
                        visibility_metrics[prompt_id] = {
                            'ai_visibility_percentage': None,
                            'ai_links_percentage': None,
                            'ai_average_position': None
                        }
                        print(f"❌ Prompt {prompt_id[:8]}: aucune analyse récente")
                    
                print(f"✅ Métriques calculées pour {len(visibility_metrics)} prompts")
            else:
                print("❌ DEBUG: Aucun prompt_id trouvé")
                    
        except Exception as e:
            # En cas d'erreur, utiliser des valeurs par défaut
            print(f"💥 ERROR: Erreur calcul métriques visibilité: {str(e)}")
            for prompt_id in [a.prompt_id for a in associations]:
                visibility_metrics[prompt_id] = {
                    'ai_visibility_percentage': None,
                    'ai_links_percentage': None,
                    'ai_average_position': None
                }
        
        return {
            'associations': [
                {
                    'prompt_id': a.prompt_id,
                    'prompt_name': a.prompt_name,
                    'keyword': a.keyword,
                    # Données SERP (Google SEO)
                    'serp_position': a.serp_position,
                    'volume': a.volume,
                    'url': a.url,
                    # Données de visibilité IA (calculées à partir des analyses récentes)
                    'ai_visibility_percentage': visibility_metrics.get(a.prompt_id, {}).get('ai_visibility_percentage'),
                    'ai_links_percentage': visibility_metrics.get(a.prompt_id, {}).get('ai_links_percentage'),
                    'ai_average_position': visibility_metrics.get(a.prompt_id, {}).get('ai_average_position'),
                    # Métadonnées d'association
                    'matching_score': a.matching_score,
                    'association_type': a.association_type
                }
                for a in associations
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
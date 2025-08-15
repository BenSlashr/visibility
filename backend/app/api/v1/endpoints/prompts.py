from typing import List, Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_database_session
from app.crud.prompt import crud_prompt
from app.crud.project import crud_project
from app.crud.ai_model import crud_ai_model
from app.schemas.prompt import (
    PromptCreate, PromptUpdate, PromptRead, PromptSummary, 
    PromptExecuteRequest, PromptExecuteResponse, PromptAIModelRead,
    BulkPromptsRequest, BulkPromptsResponse, BulkPromptResultItem
)
from app.services.execution_service import execution_service
from app.services.execution_jobs import execution_jobs
from app.core.database import SessionLocal
from app.schemas.job import JobCreateResponse, JobStatus

router = APIRouter()

@router.get("/", response_model=List[PromptSummary])
def get_prompts(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    active_only: bool = Query(False, description="Afficher seulement les prompts actifs"),
    multi_agent_only: bool = Query(False, description="Afficher seulement les prompts multi-agents"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des prompts avec filtres
    
    - **skip**: nombre d'éléments à ignorer (pagination)
    - **limit**: nombre maximum d'éléments à retourner
    - **project_id**: filtrer par projet
    - **active_only**: afficher seulement les prompts actifs
    - **multi_agent_only**: afficher seulement les prompts multi-agents
    - **search**: recherche par nom
    """
    if project_id:
        if active_only:
            prompts = crud_prompt.get_active_by_project(db, project_id)
        else:
            prompts = crud_prompt.get_by_project(db, project_id, skip=skip, limit=limit)
    elif multi_agent_only:
        prompts = crud_prompt.get_multi_agent_prompts(db, skip=skip, limit=limit)
    else:
        prompts = crud_prompt.get_multi(db, skip=skip, limit=limit)
    
    # Appliquer pagination pour les filtres si nécessaire
    if search or (project_id and active_only):
        if search:
            prompts = [p for p in prompts if search.lower() in p.name.lower()]
        prompts = prompts[skip:skip + limit]
    
    # Convertir en PromptSummary avec informations multi-agents
    result = []
    for prompt in prompts:
        # Récupérer les relations pour les informations complètes
        full_prompt = crud_prompt.get_with_relations(db, prompt.id)
        if full_prompt:
            ai_model_names = [model.name for model in full_prompt.active_ai_models]
            result.append(PromptSummary(
                id=full_prompt.id,
                project_id=full_prompt.project_id,
                name=full_prompt.name,
                description=full_prompt.description,
                template=full_prompt.template,  # Ajouté
                is_active=full_prompt.is_active,
                is_multi_agent=full_prompt.is_multi_agent or False,  # Gérer None
                ai_model_id=full_prompt.ai_model_id,  # Ajouté pour mono-agent
                ai_model_name=full_prompt.default_ai_model.name if full_prompt.default_ai_model else None,
                ai_model_names=ai_model_names,
                ai_models=[  # Ajouté pour multi-agent
                    PromptAIModelRead(
                        prompt_id=rel.prompt_id,
                        ai_model_id=rel.ai_model_id,
                        is_active=rel.is_active,
                        created_at=rel.created_at
                    ) for rel in full_prompt.ai_models  # Corrigé: ai_models au lieu de ai_model_relations
                ],
                tags=[tag.tag_name for tag in full_prompt.tags],
                last_executed_at=full_prompt.last_executed_at,
                execution_count=full_prompt.execution_count or 0,
                created_at=full_prompt.created_at,
                updated_at=full_prompt.updated_at
            ))
    
    return result

@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_database_session)
):
    """
    Crée un nouveau prompt (mode unique ou multi-agents)
    
    - **is_multi_agent**: False = utiliser ai_model_id, True = utiliser ai_model_ids
    - **ai_model_id**: Modèle unique (requis si is_multi_agent=False)
    - **ai_model_ids**: Liste des modèles (requis si is_multi_agent=True)
    """
    # Validation des paramètres selon le mode
    if prompt_in.is_multi_agent:
        if not prompt_in.ai_model_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ai_model_ids est requis pour les prompts multi-agents"
            )
        # Vérifier que tous les modèles existent et sont actifs
        for ai_model_id in prompt_in.ai_model_ids:
            model = crud_ai_model.get(db, ai_model_id)
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Modèle IA {ai_model_id} non trouvé"
                )
            if not model.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Modèle IA {model.name} n'est pas actif"
                )
    else:
        if not prompt_in.ai_model_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ai_model_id est requis pour les prompts à modèle unique"
            )
        # Vérifier que le modèle existe et est actif
        model = crud_ai_model.get(db, prompt_in.ai_model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle IA non trouvé"
            )
        if not model.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Modèle IA {model.name} n'est pas actif"
            )
    
    # Vérifier que le projet existe
    project = crud_project.get(db, prompt_in.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    # Créer le prompt
    prompt = crud_prompt.create_with_tags_and_models(db, obj_in=prompt_in)
    
    # Retourner avec les relations chargées
    return _build_prompt_read(crud_prompt.get_with_relations(db, prompt.id))

@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(
    prompt_id: str,
    db: Session = Depends(get_database_session)
):
    """Récupère un prompt par son ID"""
    prompt = crud_prompt.get_with_relations(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    return _build_prompt_read(prompt)

@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    prompt_id: str,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_database_session)
):
    """Met à jour un prompt existant"""
    prompt = crud_prompt.get(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    
    # Gérer la mise à jour des modèles si spécifiée
    if prompt_in.ai_model_ids is not None or prompt_in.is_multi_agent is not None:
        is_multi_agent = prompt_in.is_multi_agent if prompt_in.is_multi_agent is not None else prompt.is_multi_agent
        
        if is_multi_agent:
            ai_model_ids = prompt_in.ai_model_ids or []
        else:
            ai_model_ids = [prompt_in.ai_model_id] if prompt_in.ai_model_id else []
        
        if ai_model_ids:
            crud_prompt.update_models(db, prompt_id=prompt_id, ai_model_ids=ai_model_ids, is_multi_agent=is_multi_agent)
    
    # Mettre à jour les autres champs
    updated_prompt = crud_prompt.update(db, db_obj=prompt, obj_in=prompt_in)
    
    # Retourner avec les relations chargées
    return _build_prompt_read(crud_prompt.get_with_relations(db, updated_prompt.id))

@router.delete("/{prompt_id}")
def delete_prompt(
    prompt_id: str,
    db: Session = Depends(get_database_session)
):
    """Supprime un prompt"""
    prompt = crud_prompt.get(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    
    crud_prompt.remove(db, id=prompt_id)
    return {"message": "Prompt supprimé avec succès"}

@router.post("/{prompt_id}/execute", response_model=PromptExecuteResponse)
def execute_prompt(
    prompt_id: str,
    request: PromptExecuteRequest = PromptExecuteRequest(),
    db: Session = Depends(get_database_session)
):
    """
    Exécute un prompt (mode unique ou multi-agents)
    
    - **custom_variables**: Variables personnalisées pour la substitution
    - **max_tokens**: Override du nombre de tokens
    - **ai_model_ids**: Modèles spécifiques à exécuter (optionnel)
    - **compare_models**: Exécuter sur tous les modèles pour comparaison
    """
    prompt = crud_prompt.get_with_relations(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    
    if not prompt.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le prompt n'est pas actif"
        )
    
    try:
        return execution_service.execute_prompt_analysis_sync(
            db=db,
            prompt_id=prompt_id,
            custom_variables=request.custom_variables or {},
            max_tokens=request.max_tokens,
            ai_model_ids=request.ai_model_ids,
            compare_models=request.compare_models
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution: {str(e)}"
        )

@router.get("/{prompt_id}/stats")
def get_prompt_stats(
    prompt_id: str,
    db: Session = Depends(get_database_session)
):
    """Récupère les statistiques d'exécution d'un prompt"""
    prompt = crud_prompt.get(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    
    stats = crud_prompt.get_execution_stats(db, prompt_id)
    return stats

@router.put("/{prompt_id}/models/{ai_model_id}/toggle")
def toggle_model_active(
    prompt_id: str,
    ai_model_id: str,
    is_active: bool = Query(..., description="Activer ou désactiver le modèle"),
    db: Session = Depends(get_database_session)
):
    """Active/désactive un modèle IA spécifique pour un prompt multi-agents"""
    prompt = crud_prompt.get(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt non trouvé"
        )
    
    if not prompt.is_multi_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette opération n'est disponible que pour les prompts multi-agents"
        )
    
    success = crud_prompt.toggle_model_active(db, prompt_id=prompt_id, ai_model_id=ai_model_id, is_active=is_active)
    if success:
        return {"message": f"Modèle {'activé' if is_active else 'désactivé'} avec succès"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour"
        )


# --- Exécution batch asynchrone ---
@router.post("/execute-all", response_model=JobCreateResponse)
async def execute_all_prompts(
    project_id: str = Query(...),
):
    """
    Déclenche un job asynchrone qui exécute tous les prompts actifs d'un projet.
    Retourne immédiatement un job_id; interroger /prompts/jobs/{job_id} pour le statut.
    """
    job = execution_jobs.create_job()

    async def _runner():
        await execution_jobs.run_project_prompts(SessionLocal, project_id)

    asyncio.create_task(_runner())

    return JobCreateResponse(job_id=job.job_id, status=job.status, created_at=job.created_at)


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    job = execution_jobs.get_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        total_items=job.total_items,
        processed_items=job.processed_items,
        success_count=job.success_count,
        error_count=job.error_count,
        errors=job.errors,
        results=job.results,
    )

def _build_prompt_read(prompt) -> PromptRead:
    """Construit un PromptRead à partir d'un modèle Prompt avec relations"""
    if not prompt:
        return None
    
    ai_models_data = []
    for pam in prompt.ai_models:
        ai_models_data.append({
            'prompt_id': pam.prompt_id,
            'ai_model_id': pam.ai_model_id,
            'is_active': pam.is_active,
            'created_at': pam.created_at,
            'ai_model_name': pam.ai_model.name if pam.ai_model else None,
            'ai_model_provider': pam.ai_model.provider if pam.ai_model else None
        })
    
    return PromptRead(
        id=prompt.id,
        project_id=prompt.project_id,
        name=prompt.name,
        description=prompt.description,
        template=prompt.template,
        is_active=prompt.is_active,
        is_multi_agent=prompt.is_multi_agent,
        ai_model_id=prompt.ai_model_id,
        last_executed_at=prompt.last_executed_at,
        execution_count=prompt.execution_count or 0,
        tags=[tag.tag_name for tag in prompt.tags],
        ai_models=ai_models_data,
        ai_model_name=prompt.default_ai_model.name if prompt.default_ai_model else None,
        ai_model_names=[model.name for model in prompt.active_ai_models],
        created_at=prompt.created_at,
        updated_at=prompt.updated_at
    ) 


# --- Importation en masse ---
@router.post("/bulk", response_model=BulkPromptsResponse)
def bulk_create_prompts(
    request: BulkPromptsRequest,
    db: Session = Depends(get_database_session)
):
    """
    Crée ou met à jour des prompts en masse.
    - validate_only: si true, ne crée rien et retourne les erreurs éventuelles
    - upsert_by: 'name' pour upsert par nom (par projet)
    - defaults: champs par défaut appliqués aux items manquants
    """
    results: list[BulkPromptResultItem] = []
    success = 0
    errors = 0

    for idx, item in enumerate(request.items):
        item_errors: list[str] = []
        data = {**(request.defaults or {}), **item.dict()}

        # Validation minimale
        if not data.get('project_id'):
            item_errors.append('project_id manquant')
        if not data.get('name'):
            item_errors.append('name manquant')
        if not data.get('template'):
            item_errors.append('template manquant')

        is_multi = bool(data.get('is_multi_agent'))

        # Résolution par nom si fourni
        resolved_ai_model_id = data.get('ai_model_id')
        resolved_ai_model_ids = list(data.get('ai_model_ids') or [])
        if not resolved_ai_model_id and data.get('ai_model_name'):
            model = crud_ai_model.get_by_name(db, data['ai_model_name'])
            if model:
                resolved_ai_model_id = model.id
            else:
                item_errors.append(f"Modèle IA '{data.get('ai_model_name')}' introuvable")
        if not resolved_ai_model_id and data.get('ai_model_identifier'):
            model = crud_ai_model.get_by_identifier(db, data['ai_model_identifier'])
            if model:
                resolved_ai_model_id = model.id
            else:
                item_errors.append(f"Identifiant de modèle IA '{data.get('ai_model_identifier')}' introuvable")
        if not resolved_ai_model_ids and data.get('ai_model_names'):
            for name in data.get('ai_model_names'):
                m = crud_ai_model.get_by_name(db, name)
                if m:
                    resolved_ai_model_ids.append(m.id)
                else:
                    item_errors.append(f"Modèle IA '{name}' introuvable")
        if not resolved_ai_model_ids and data.get('ai_model_identifiers'):
            for ident in data.get('ai_model_identifiers'):
                m = crud_ai_model.get_by_identifier(db, ident)
                if m:
                    resolved_ai_model_ids.append(m.id)
                else:
                    item_errors.append(f"Identifiant de modèle IA '{ident}' introuvable")

        # Exigences selon le mode (après résolution)
        if is_multi and len(resolved_ai_model_ids) == 0:
            item_errors.append('ai_model_ids ou ai_model_names requis pour is_multi_agent=true')
        if not is_multi and not resolved_ai_model_id:
            item_errors.append('ai_model_id ou ai_model_name requis pour is_multi_agent=false')

        # Validations de base en base de données (projet + modèles)
        # Projet
        if data.get('project_id'):
            project = crud_project.get(db, data['project_id'])
            if not project:
                item_errors.append('Projet introuvable')
        # Modèles IA

        if is_multi:
            for mid in (resolved_ai_model_ids or []):
                model = crud_ai_model.get(db, mid)
                if not model:
                    item_errors.append(f"Modèle IA {mid} introuvable")
                elif not model.is_active:
                    item_errors.append(f"Modèle IA {model.name} inactif")
        else:
            if resolved_ai_model_id:
                model = crud_ai_model.get(db, resolved_ai_model_id)
                if not model:
                    item_errors.append('Modèle IA introuvable')
                elif not model.is_active:
                    item_errors.append(f"Modèle IA {model.name} inactif")

        if item_errors:
            errors += 1
            results.append(BulkPromptResultItem(index=idx, status='error', errors=item_errors))
            continue

        if request.validate_only:
            results.append(BulkPromptResultItem(index=idx, status='validated'))
            success += 1
            continue

        # Upsert par nom au sein du projet
        existing_id = None
        if request.upsert_by == 'name':
            existing = crud_prompt.get_by_project_and_name(db, data['project_id'], data['name'])
            if existing:
                existing_id = existing.id

        try:
            if existing_id:
                # update
                updated = crud_prompt.update(db, db_obj=existing, obj_in=PromptUpdate(**{
                    'description': data.get('description'),
                    'template': data.get('template'),
                    'tags': data.get('tags'),
                    'is_active': data.get('is_active'),
                    'is_multi_agent': data.get('is_multi_agent'),
                    'ai_model_id': resolved_ai_model_id,
                    'ai_model_ids': resolved_ai_model_ids,
                }))
                # mettre à jour les modèles si nécessaire
                if is_multi:
                    crud_prompt.update_models(db, prompt_id=updated.id, ai_model_ids=resolved_ai_model_ids, is_multi_agent=True)
                else:
                    crud_prompt.update_models(db, prompt_id=updated.id, ai_model_ids=[resolved_ai_model_id] if resolved_ai_model_id else [], is_multi_agent=False)
                results.append(BulkPromptResultItem(index=idx, status='updated', id=updated.id))
                success += 1
            else:
                created = crud_prompt.create_with_tags_and_models(db, obj_in=PromptCreate(**{
                    'project_id': data['project_id'],
                    'name': data['name'],
                    'description': data.get('description'),
                    'template': data['template'],
                    'tags': data.get('tags', []),
                    'is_active': data.get('is_active', True),
                    'is_multi_agent': data.get('is_multi_agent', False),
                    'ai_model_id': resolved_ai_model_id,
                    'ai_model_ids': resolved_ai_model_ids,
                }))
                results.append(BulkPromptResultItem(index=idx, status='created', id=created.id))
                success += 1
        except Exception as e:
            # Important: rollback pour pouvoir continuer le lot
            try:
                db.rollback()
            except Exception:
                pass
            errors += 1
            results.append(BulkPromptResultItem(index=idx, status='error', errors=[str(e)]))

    return BulkPromptsResponse(success_count=success, error_count=errors, results=results)
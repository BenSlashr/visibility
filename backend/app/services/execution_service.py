import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from .ai_service import ai_service, AIServiceError
from .prompt_service import prompt_service, PromptServiceError
from .analysis_service import analysis_service, AnalysisServiceError
from ..crud.prompt import crud_prompt
from ..crud.analysis import crud_analysis
from ..crud.analysis_source import crud_analysis_source
from .sources.extractor import source_extractor
from urllib.parse import urlparse
from ..models.prompt import Prompt
from ..models.analysis import Analysis, AnalysisCompetitor
from ..schemas.analysis import AnalysisCreate, AnalysisCompetitorCreate

logger = logging.getLogger(__name__)

class ExecutionServiceError(Exception):
    """Exception personnalisée pour les erreurs du service d'exécution"""
    pass

class ExecutionService:
    """
    Service d'orchestration pour l'exécution complète d'analyses
    Combine prompt_service, ai_service et analysis_service
    """
    
    def __init__(self):
        self.ai_service = ai_service
        self.prompt_service = prompt_service
        self.analysis_service = analysis_service
    
    async def execute_prompt_analysis(
        self,
        db: Session,
        prompt_id: str,
        custom_variables: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
        ai_model_ids: Optional[List[str]] = None,
        compare_models: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute une analyse complète à partir d'un prompt
        
        Args:
            db: Session de base de données
            prompt_id: ID du prompt à exécuter
            custom_variables: Variables personnalisées pour la substitution
            max_tokens: Override du nombre de tokens
            
        Returns:
            Dict avec les résultats complets de l'analyse
        """
        execution_start = datetime.utcnow()
        
        try:
            # 1. Récupérer le prompt avec ses relations
            prompt = crud_prompt.get_with_relations(db, prompt_id)
            if not prompt:
                raise ExecutionServiceError(f"Prompt {prompt_id} non trouvé")
            
            if not prompt.is_active:
                raise ExecutionServiceError(f"Le prompt '{prompt.name}' n'est pas actif")
            
            # 2. Déterminer les modèles IA à utiliser (mono ou multi-agents)
            if prompt.is_multi_agent or compare_models:
                ai_models = prompt.active_ai_models
                if not ai_models:
                    raise ExecutionServiceError("Aucun modèle IA actif pour ce prompt multi-agents")
                # Restreindre aux modèles explicitement demandés si fournis
                if ai_model_ids:
                    ai_models = [m for m in ai_models if m.id in set(ai_model_ids)]
                    if not ai_models:
                        raise ExecutionServiceError("Aucun des modèles demandés n'est actif ou associé au prompt")
            else:
                if not prompt.ai_model or not prompt.ai_model.is_active:
                    raise ExecutionServiceError("Le modèle IA n'est pas configuré ou inactif")
                ai_models = [prompt.ai_model]
            
            # 3. Substituer les variables dans le prompt
            logger.info(f"Substitution des variables pour le prompt {prompt.name}")
            project_variables = self.prompt_service.get_project_variables(db, prompt.project)
            substitution_result = self.prompt_service.substitute_variables(
                prompt.template,
                project_variables,
                custom_variables
            )
            
            if not substitution_result['success']:
                raise ExecutionServiceError(f"Erreur de substitution: {substitution_result['error']}")
            
            final_prompt = substitution_result['prompt']
            variables_used = substitution_result['variables_used']
            
            # 4. Exécuter le prompt avec l'IA (pour chaque modèle sélectionné)
            logger.info("Exécution du prompt avec %d modèle(s)", len(ai_models))
            async def run_model(model):
                result = await self.ai_service.execute_prompt(model, final_prompt, max_tokens)
                if not result['success']:
                    raise ExecutionServiceError(f"Erreur IA: {result['error']}")
                return {**result, 'model': model}

            ai_results: List[Dict[str, Any]] = await asyncio.gather(*[run_model(m) for m in ai_models])
            
            # 5. Analyser la réponse IA
            logger.info("Analyse des réponses IA et persistance des analyses")
            created_analyses = []
            # Préparer l'ensemble des domaines concurrents (normalisés) pour filtrage des sources
            competitor_domains = set()
            try:
                if prompt.project and getattr(prompt.project, 'competitors', None):
                    for comp in prompt.project.competitors:
                        comp_site = (comp.website or '').strip()
                        if not comp_site:
                            continue
                        # Normaliser domaine
                        try:
                            parsed = urlparse(comp_site if comp_site.startswith('http') else f'http://{comp_site}')
                            host = parsed.netloc.lower()
                            if host.startswith('www.'):
                                host = host[4:]
                            if host:
                                competitor_domains.add(host)
                        except Exception:
                            continue
            except Exception:
                competitor_domains = set()

            for ai_result in ai_results:
                analysis_result = self.analysis_service.analyze_response(
                    db,
                    ai_result['ai_response'],
                    prompt.project,
                    prompt.project.competitors
                )
                analysis_data = AnalysisCreate(
                    prompt_id=prompt.id,
                    project_id=prompt.project_id,
                    prompt_executed=final_prompt,
                    ai_response=ai_result['ai_response'],
                    variables_used=variables_used,
                    brand_mentioned=analysis_result['brand_mentioned'],
                    website_mentioned=analysis_result['website_mentioned'],
                    website_linked=analysis_result['website_linked'],
                    ranking_position=analysis_result['ranking_position'],
                    ai_model_used=ai_result['ai_model_used'],
                    tokens_used=ai_result['tokens_used'],
                    processing_time_ms=ai_result['processing_time_ms'],
                    cost_estimated=ai_result['cost_estimated'],
                    web_search_used=bool(ai_result.get('web_search_used', False)),
                    competitor_analyses=[
                        AnalysisCompetitorCreate(
                            competitor_name=comp_name,
                            is_mentioned=True,
                            ranking_position=None,
                            mention_context=details['context'][0] if details['context'] else ''
                        )
                        for comp_name, details in analysis_result['competitors_analysis'].items()
                    ]
                )
                db_analysis = crud_analysis.create_with_competitors(db, obj_in=analysis_data)

                # 6. Extraire et persister les sources
                try:
                    sources = source_extractor.extract(ai_result['ai_response'])
                    # Filtrer: exclure les domaines concurrents
                    if sources and competitor_domains:
                        def is_competitor_domain(domain: str) -> bool:
                            if not domain:
                                return False
                            d = domain.lower()
                            # Match suffix pour couvrir les sous-domaines
                            return any(d == cd or d.endswith('.' + cd) for cd in competitor_domains)
                        sources = [s for s in sources if not is_competitor_domain((s.domain or ''))]
                    if sources:
                        crud_analysis_source.create_bulk_for_analysis(db, db_analysis.id, sources)
                except Exception as e:
                    logger.warning(f"Extraction des sources échouée pour analysis {db_analysis.id}: {e}")
                created_analyses.append((db_analysis, analysis_result, ai_result))
            
            # Incrémenter le compteur d'exécution du prompt (une fois)
            crud_prompt.increment_execution_count(db, prompt_id=prompt.id)
            
            # 8. Calculer le temps total d'exécution
            execution_end = datetime.utcnow()
            total_execution_time = int((execution_end - execution_start).total_seconds() * 1000)
            
            logger.info("Analyse terminée avec succès (%d exécutions)", len(created_analyses))
            
            # Si un seul modèle exécuté, retourner les champs de compatibilité
            if len(created_analyses) == 1:
                db_analysis, analysis_result, ai_result = created_analyses[0]
                return {
                    'success': True,
                    'analysis_id': db_analysis.id,
                    'prompt_name': prompt.name,
                    'project_name': prompt.project.name,
                    'ai_model_used': ai_result['ai_model_used'],
                    'prompt_executed': final_prompt,
                    'ai_response': ai_result['ai_response'],
                    'variables_used': variables_used,
                    # Champs à plat pour compatibilité UI
                    'brand_mentioned': analysis_result.get('brand_mentioned'),
                    'website_mentioned': analysis_result.get('website_mentioned'),
                    'website_linked': analysis_result.get('website_linked'),
                    'ranking_position': analysis_result.get('ranking_position'),
                    'visibility_score': analysis_result.get('visibility_score'),
                    'analysis_results': analysis_result,
                    'execution_metrics': {
                        'total_execution_time_ms': total_execution_time,
                        'ai_processing_time_ms': ai_result['processing_time_ms'],
                        'tokens_used': ai_result['tokens_used'],
                        'cost_estimated': ai_result['cost_estimated']
                    },
                    'error': None
                }
            
            # Multi-agents: retourner la liste et les agrégations
            analyses_payload = []
            total_cost = 0.0
            total_tokens = 0
            for db_analysis, analysis_result, ai_result in created_analyses:
                analyses_payload.append({
                    'analysis_id': db_analysis.id,
                    'ai_model_used': ai_result['ai_model_used'],
                    'ai_response': ai_result['ai_response'],
                    'tokens_used': ai_result['tokens_used'],
                    'processing_time_ms': ai_result['processing_time_ms'],
                    'cost_estimated': ai_result['cost_estimated'],
                    'analysis_results': analysis_result
                })
                total_cost += ai_result['cost_estimated']
                total_tokens += ai_result['tokens_used']
            
            return {
                'success': True,
                'prompt_name': prompt.name,
                'project_name': prompt.project.name,
                'prompt_executed': final_prompt,
                'variables_used': variables_used,
                'analyses': analyses_payload,
                'total_cost': total_cost,
                'comparison_summary': {
                    'models': [a['ai_model_used'] for a in analyses_payload],
                    'best_visibility': max((r['analysis_results']['visibility_score'] for r in analyses_payload), default=0),
                    'total_tokens': total_tokens
                },
                'execution_metrics': {
                    'total_execution_time_ms': total_execution_time
                },
                'error': None
            }
            
        except Exception as e:
            execution_end = datetime.utcnow()
            total_execution_time = int((execution_end - execution_start).total_seconds() * 1000)
            
            error_msg = f"Erreur lors de l'exécution: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'analysis_id': None,
                'prompt_name': prompt.name if 'prompt' in locals() else 'Inconnu',
                'project_name': prompt.project.name if 'prompt' in locals() and prompt.project else 'Inconnu',
                'ai_model_used': prompt.ai_model.name if 'prompt' in locals() and prompt.ai_model else 'Inconnu',
                'prompt_executed': '',
                'ai_response': '',
                'variables_used': {},
                'analysis_results': {},
                'execution_metrics': {
                    'total_execution_time_ms': total_execution_time,
                    'ai_processing_time_ms': 0,
                    'tokens_used': 0,
                    'cost_estimated': 0.0
                },
                'error': error_msg
            }

    def execute_prompt_analysis_sync(
        self,
        db: Session,
        prompt_id: str,
        custom_variables: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None,
        ai_model_ids: Optional[List[str]] = None,
        compare_models: bool = False
    ) -> Dict[str, Any]:
        """
        Version synchrone de l'exécution, adaptée aux endpoints sync.
        Orchestration multi-modèles séquentielle ou parallèle (via asyncio.run).
        """
        # Pour simplifier le chemin critique, on exécute via l'async interne
        async def _run():
            # Si des modèles sont explicitement fournis et compare_models, on patch le prompt dynamiquement
            # en restreignant la liste des modèles actifs à ceux demandés.
            # On laisse la logique principale gérer le reste.
            return await self.execute_prompt_analysis(
                db=db,
                prompt_id=prompt_id,
                custom_variables=custom_variables,
                max_tokens=max_tokens,
                ai_model_ids=ai_model_ids,
                compare_models=compare_models
            )
        return asyncio.run(_run())
    
    async def execute_multiple_prompts(
        self,
        db: Session,
        prompt_ids: List[str],
        custom_variables: Optional[Dict[str, str]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécute plusieurs prompts en séquence
        
        Args:
            db: Session de base de données
            prompt_ids: Liste des IDs de prompts à exécuter
            custom_variables: Variables personnalisées
            max_tokens: Override du nombre de tokens
            
        Returns:
            Dict avec les résultats de toutes les exécutions
        """
        start_time = datetime.utcnow()
        results = []
        successful_executions = 0
        total_cost = 0.0
        total_tokens = 0
        
        logger.info(f"Exécution de {len(prompt_ids)} prompts")
        
        for i, prompt_id in enumerate(prompt_ids):
            logger.info(f"Exécution {i+1}/{len(prompt_ids)}: prompt {prompt_id}")
            
            try:
                result = await self.execute_prompt_analysis(
                    db, prompt_id, custom_variables, max_tokens
                )
                results.append(result)
                
                if result['success']:
                    successful_executions += 1
                    total_cost += result['execution_metrics']['cost_estimated']
                    total_tokens += result['execution_metrics']['tokens_used']
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du prompt {prompt_id}: {e}")
                results.append({
                    'success': False,
                    'prompt_id': prompt_id,
                    'error': str(e)
                })
        
        end_time = datetime.utcnow()
        total_time = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            'total_prompts': len(prompt_ids),
            'successful_executions': successful_executions,
            'failed_executions': len(prompt_ids) - successful_executions,
            'total_execution_time_ms': total_time,
            'total_cost_estimated': total_cost,
            'total_tokens_used': total_tokens,
            'results': results
        }
    
    def get_execution_preview(
        self,
        db: Session,
        prompt_id: str,
        custom_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Génère un aperçu de l'exécution sans appeler l'IA
        
        Args:
            db: Session de base de données
            prompt_id: ID du prompt
            custom_variables: Variables personnalisées
            
        Returns:
            Dict avec l'aperçu de l'exécution
        """
        try:
            # Récupérer le prompt
            prompt = crud_prompt.get_with_relations(db, prompt_id)
            if not prompt:
                raise ExecutionServiceError(f"Prompt {prompt_id} non trouvé")
            
            # Générer l'aperçu du prompt
            preview = self.prompt_service.get_template_preview(
                db, prompt, custom_variables
            )
            
            # Ajouter des informations sur l'exécution
            preview['execution_info'] = {
                'prompt_name': prompt.name,
                'project_name': prompt.project.name,
                'ai_model': prompt.ai_model.name,
                'ai_provider': prompt.ai_model.provider,
                'max_tokens': prompt.ai_model.max_tokens,
                'estimated_cost_per_execution': prompt.ai_model.cost_per_1k_tokens * (prompt.ai_model.max_tokens / 1000),
                'prompt_active': prompt.is_active,
                'model_active': prompt.ai_model.is_active,
                'can_execute': prompt.is_active and prompt.ai_model.is_active and preview['success']
            }
            
            return preview
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'aperçu: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'execution_info': {}
            }
    
    async def validate_execution_requirements(
        self,
        db: Session,
        prompt_id: str
    ) -> Dict[str, Any]:
        """
        Valide que toutes les conditions sont réunies pour l'exécution
        
        Args:
            db: Session de base de données
            prompt_id: ID du prompt à valider
            
        Returns:
            Dict avec le statut de validation
        """
        try:
            issues = []
            warnings = []
            
            # Récupérer le prompt
            prompt = crud_prompt.get_with_relations(db, prompt_id)
            if not prompt:
                issues.append("Prompt non trouvé")
                return {'valid': False, 'issues': issues, 'warnings': warnings}
            
            # Vérifier le prompt
            if not prompt.is_active:
                issues.append("Le prompt n'est pas actif")
            
            # Vérifier le modèle IA
            if not prompt.ai_model:
                issues.append("Aucun modèle IA associé")
            elif not prompt.ai_model.is_active:
                issues.append(f"Le modèle IA '{prompt.ai_model.name}' n'est pas actif")
            
            # Vérifier les clés API
            if prompt.ai_model:
                api_test = await self.ai_service.test_api_key(prompt.ai_model.provider)
                if not api_test['valid']:
                    issues.append(f"Clé API {prompt.ai_model.provider} invalide: {api_test['error']}")
            
            # Vérifier le template
            template_validation = self.prompt_service.validate_template(prompt.template)
            if not template_validation['valid']:
                issues.append(f"Template invalide: {template_validation['error']}")
            
            # Vérifier les variables
            project_variables = self.prompt_service.get_project_variables(db, prompt.project)
            substitution_test = self.prompt_service.substitute_variables(
                prompt.template, project_variables
            )
            if not substitution_test['success']:
                issues.append(f"Variables manquantes: {substitution_test['error']}")
            
            # Avertissements
            if not prompt.project.keywords:
                warnings.append("Aucun mot-clé défini pour le projet")
            
            if not prompt.project.competitors:
                warnings.append("Aucun concurrent défini pour le projet")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'prompt_name': prompt.name,
                'project_name': prompt.project.name,
                'ai_model_name': prompt.ai_model.name if prompt.ai_model else 'Aucun'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {e}", exc_info=True)
            return {
                'valid': False,
                'issues': [f"Erreur de validation: {str(e)}"],
                'warnings': []
            }

# Instance globale du service
execution_service = ExecutionService() 
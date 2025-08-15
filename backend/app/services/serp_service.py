import csv
import io
import unicodedata
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.serp import SERPImport, SERPKeyword, PromptSERPAssociation
from ..models.prompt import Prompt
from ..models.project import ProjectKeyword
from ..crud.base import CRUDBase

logger = logging.getLogger(__name__)

class SERPServiceError(Exception):
    """Exception personnalisée pour les erreurs du service SERP"""
    pass

class SERPService:
    """Service pour gérer les données SERP et les associations avec les prompts"""
    
    def __init__(self):
        pass
    
    def normalize_text(self, text: str) -> str:
        """Normalise le texte : minuscules, supprime accents, gère pluriels"""
        if not text:
            return ""
        
        # Minuscules
        text = text.lower()
        
        # Supprimer accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        # Supprimer pluriels simples (s, x, z en fin de mot)
        text = re.sub(r'\b(\w+)[sxz]\b', r'\1', text)
        
        return text
    
    def extract_words(self, text: str) -> set:
        """Extrait les mots normalisés d'un texte"""
        normalized = self.normalize_text(text)
        words = re.findall(r'\b\w+\b', normalized)
        return set(w for w in words if len(w) > 2)  # Ignorer mots < 3 lettres
    
    def import_csv(
        self, 
        db: Session, 
        project_id: str, 
        csv_content: str, 
        filename: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Importe un CSV de positionnement SERP
        Format attendu: keyword,volume,position,url
        """
        try:
            # Désactiver l'import précédent s'il existe
            previous_import = db.query(SERPImport).filter(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            ).first()
            
            if previous_import:
                previous_import.is_active = False
                db.commit()
                logger.info(f"Import précédent {previous_import.id} désactivé")
            
            # Créer nouvel import
            serp_import = SERPImport(
                project_id=project_id,
                filename=filename,
                notes=notes,
                is_active=True
            )
            db.add(serp_import)
            db.flush()  # Pour obtenir l'ID
            
            # Parser le CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            keywords_imported = []
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # Start=2 car ligne 1 = header
                try:
                    # Validation des champs requis
                    if not row.get('keyword'):
                        errors.append(f"Ligne {row_num}: mot-clé manquant")
                        continue
                    
                    if not row.get('position'):
                        errors.append(f"Ligne {row_num}: position manquante")
                        continue
                    
                    # Créer le keyword SERP
                    keyword = row['keyword'].strip()
                    serp_keyword = SERPKeyword(
                        import_id=serp_import.id,
                        project_id=project_id,
                        keyword=keyword,
                        keyword_normalized=self.normalize_text(keyword),
                        volume=int(row.get('volume', 0)) if row.get('volume') else None,
                        position=int(row['position']),
                        url=row.get('url', '').strip() or None
                    )
                    
                    db.add(serp_keyword)
                    keywords_imported.append(serp_keyword)
                    
                except ValueError as e:
                    errors.append(f"Ligne {row_num}: erreur format ({str(e)})")
                except Exception as e:
                    errors.append(f"Ligne {row_num}: erreur inconnue ({str(e)})")
            
            # Mettre à jour le compteur
            serp_import.total_keywords = len(keywords_imported)
            db.commit()
            
            logger.info(f"Import SERP réussi: {len(keywords_imported)} mots-clés importés")
            
            return {
                'success': True,
                'import_id': serp_import.id,
                'keywords_imported': len(keywords_imported),
                'errors_count': len(errors),
                'errors': errors[:10]  # Limiter à 10 erreurs pour l'affichage
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur import CSV SERP: {str(e)}")
            raise SERPServiceError(f"Erreur lors de l'import: {str(e)}")
    
    def calculate_matching_score(self, prompt: Prompt, serp_keyword: SERPKeyword) -> float:
        """Calcule le score de matching entre un prompt et un mot-clé SERP"""
        score = 0.0
        
        # 1. EXACT MATCH dans les mots-clés projet (poids: 40%)
        project_keywords_normalized = [
            self.normalize_text(kw.keyword) 
            for kw in prompt.project.keywords
        ]
        
        if serp_keyword.keyword_normalized in project_keywords_normalized:
            score += 0.4
        
        # 2. PRÉSENCE dans le template (poids: 35%)  
        template_words = self.extract_words(prompt.template)
        keyword_words = self.extract_words(serp_keyword.keyword)
        
        if keyword_words:
            # Calculer intersection des mots
            intersection = template_words.intersection(keyword_words)
            word_match_ratio = len(intersection) / len(keyword_words)
            score += 0.35 * word_match_ratio
        
        # 3. SIMILARITÉ nom/description (poids: 25%)
        prompt_text = f"{prompt.name} {prompt.description or ''}"
        prompt_words = self.extract_words(prompt_text)
        
        if keyword_words and prompt_words:
            intersection = prompt_words.intersection(keyword_words)
            union = prompt_words.union(keyword_words)
            jaccard_similarity = len(intersection) / len(union) if union else 0
            score += 0.25 * jaccard_similarity
        
        return min(score, 1.0)  # Cap à 1.0
    
    def auto_match_prompts_to_keywords(self, db: Session, project_id: str) -> Dict[str, Any]:
        """Associe automatiquement les prompts aux mots-clés SERP"""
        try:
            # Récupérer l'import actif
            serp_import = db.query(SERPImport).filter(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            ).first()
            
            if not serp_import:
                raise SERPServiceError("Aucun import SERP actif trouvé pour ce projet")
            
            # Récupérer prompts et keywords
            prompts = db.query(Prompt).filter(Prompt.project_id == project_id).all()
            keywords = serp_import.keywords
            
            auto_matches = []
            suggestions = []
            
            # Supprimer associations automatiques existantes
            db.query(PromptSERPAssociation).filter(
                PromptSERPAssociation.prompt_id.in_([p.id for p in prompts]),
                PromptSERPAssociation.association_type == 'auto'
            ).delete(synchronize_session=False)
            
            # Calculer scores pour chaque combinaison
            for prompt in prompts:
                best_keyword = None
                best_score = 0.0
                
                for keyword in keywords:
                    score = self.calculate_matching_score(prompt, keyword)
                    
                    if score > best_score:
                        best_score = score
                        best_keyword = keyword
                
                # Créer association selon le score
                if best_score >= 0.7:  # Association automatique
                    association = PromptSERPAssociation(
                        prompt_id=prompt.id,
                        serp_keyword_id=best_keyword.id,
                        matching_score=best_score,
                        association_type='auto'
                    )
                    db.add(association)
                    auto_matches.append({
                        'prompt_id': prompt.id,
                        'prompt_name': prompt.name,
                        'keyword': best_keyword.keyword,
                        'score': best_score
                    })
                
                elif best_score >= 0.4:  # Suggestion
                    suggestions.append({
                        'prompt_id': prompt.id,
                        'prompt_name': prompt.name,
                        'keyword': best_keyword.keyword,
                        'keyword_id': best_keyword.id,
                        'score': best_score
                    })
            
            db.commit()
            
            return {
                'success': True,
                'auto_matches': len(auto_matches),
                'suggestions': len(suggestions),
                'details': {
                    'auto_matches': auto_matches,
                    'suggestions': suggestions
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur auto-matching: {str(e)}")
            raise SERPServiceError(f"Erreur lors de l'association automatique: {str(e)}")
    
    async def get_matching_suggestions(self, project_id: str, db: Session) -> Dict[str, Any]:
        """
        Récupère les suggestions de matching pour les prompts non associés
        """
        try:
            # Récupérer l'import actif
            active_import = db.query(SERPImport).filter(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            ).first()
            
            if not active_import:
                return {'success': False, 'message': 'Aucun import SERP actif trouvé'}
            
            # Récupérer les prompts non associés (optimisé)
            associated_prompt_ids = db.query(PromptSERPAssociation.prompt_id).join(
                Prompt, PromptSERPAssociation.prompt_id == Prompt.id
            ).filter(
                Prompt.project_id == project_id
            ).subquery()
            
            prompts = db.query(Prompt).filter(
                Prompt.project_id == project_id,
                ~Prompt.id.in_(associated_prompt_ids)
            ).all()  # Tous les prompts non associés
            
            # Récupérer tous les mots-clés
            keywords = db.query(SERPKeyword).filter(
                SERPKeyword.import_id == active_import.id
            ).order_by(SERPKeyword.position).all()
            
            suggestions = []
            
            for prompt in prompts:
                best_keyword = None
                best_score = 0.0
                
                # Optimisation: on s'arrête si on trouve un score parfait
                for keyword in keywords:
                    score = self.calculate_matching_score(prompt, keyword)
                    
                    if score > best_score:
                        best_score = score
                        best_keyword = keyword
                        
                        # Si le score est parfait, pas besoin de continuer
                        if score >= 0.95:
                            break
                
                # Suggestion pour scores entre 0.4 et 0.7
                if best_score >= 0.4 and best_score < 0.7:
                    confidence_level = 'high' if best_score >= 0.6 else 'medium' if best_score >= 0.5 else 'low'
                    
                    suggestions.append({
                        'prompt_id': prompt.id,
                        'prompt_name': prompt.name,
                        'keyword': best_keyword.keyword,
                        'keyword_id': best_keyword.id,
                        'score': best_score,
                        'confidence_level': confidence_level
                    })
            
            return {
                'success': True,
                'suggestions': suggestions,
                'stats': {
                    'total_prompts_analyzed': len(prompts),
                    'total_keywords_available': len(keywords),
                    'total_calculations': len(prompts) * len(keywords)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération suggestions: {str(e)}")
            raise SERPServiceError(f"Erreur lors de la récupération des suggestions: {str(e)}")
    
    def set_manual_association(
        self, 
        db: Session, 
        prompt_id: str, 
        serp_keyword_id: Optional[str]
    ) -> Dict[str, Any]:
        """Définit manuellement l'association entre un prompt et un mot-clé SERP"""
        try:
            # Supprimer association existante pour ce prompt
            db.query(PromptSERPAssociation).filter(
                PromptSERPAssociation.prompt_id == prompt_id
            ).delete()
            
            if serp_keyword_id:
                # Créer nouvelle association
                association = PromptSERPAssociation(
                    prompt_id=prompt_id,
                    serp_keyword_id=serp_keyword_id,
                    association_type='manual'
                )
                db.add(association)
            
            db.commit()
            
            return {'success': True}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur association manuelle: {str(e)}")
            raise SERPServiceError(f"Erreur lors de l'association manuelle: {str(e)}")
    
    def get_project_serp_summary(self, db: Session, project_id: str) -> Dict[str, Any]:
        """Récupère le résumé SERP d'un projet"""
        try:
            # Import actif
            serp_import = db.query(SERPImport).filter(
                SERPImport.project_id == project_id,
                SERPImport.is_active == True
            ).first()
            
            if not serp_import:
                return {
                    'has_serp_data': False,
                    'message': 'Aucune donnée SERP importée'
                }
            
            # Statistiques générales
            total_keywords = len(serp_import.keywords)
            avg_position = sum(k.position for k in serp_import.keywords) / total_keywords if total_keywords > 0 else 0
            
            # Associations
            associations = db.query(PromptSERPAssociation).join(SERPKeyword).filter(
                SERPKeyword.project_id == project_id
            ).all()
            
            auto_associations = [a for a in associations if a.association_type == 'auto']
            manual_associations = [a for a in associations if a.association_type == 'manual']
            
            # Prompts sans association
            all_prompts = db.query(Prompt).filter(Prompt.project_id == project_id).count()
            associated_prompts = len(set(a.prompt_id for a in associations))
            unassociated_prompts = all_prompts - associated_prompts
            
            return {
                'has_serp_data': True,
                'import_info': {
                    'filename': serp_import.filename,
                    'import_date': serp_import.import_date.isoformat(),
                    'total_keywords': total_keywords
                },
                'serp_stats': {
                    'average_position': round(avg_position, 1),
                    'top_3_keywords': len([k for k in serp_import.keywords if k.position <= 3]),
                    'top_10_keywords': len([k for k in serp_import.keywords if k.position <= 10])
                },
                'associations': {
                    'auto_associations': len(auto_associations),
                    'manual_associations': len(manual_associations),
                    'unassociated_prompts': unassociated_prompts,
                    'association_rate': round((associated_prompts / all_prompts * 100), 1) if all_prompts > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé SERP: {str(e)}")
            raise SERPServiceError(f"Erreur lors de la récupération du résumé: {str(e)}")

# Instance globale du service
serp_service = SERPService()
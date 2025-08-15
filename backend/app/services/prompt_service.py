import re
import logging
from typing import Dict, List, Set, Any, Optional
from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.prompt import Prompt

logger = logging.getLogger(__name__)

class PromptServiceError(Exception):
    """Exception personnalisée pour les erreurs du service de prompts"""
    pass

class PromptService:
    """
    Service pour la gestion et la substitution des variables dans les prompts
    """
    
    def __init__(self):
        # Pattern pour détecter les variables {variable_name}
        self.variable_pattern = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
    
    def extract_variables(self, template: str) -> Set[str]:
        """
        Extrait toutes les variables d'un template de prompt
        
        Args:
            template: Template du prompt avec variables {variable}
            
        Returns:
            Set des noms de variables trouvées
        """
        return set(self.variable_pattern.findall(template))
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """
        Valide un template de prompt
        
        Args:
            template: Template à valider
            
        Returns:
            Dict avec le statut de validation et les détails
        """
        if not template.strip():
            return {
                'valid': False,
                'error': 'Le template ne peut pas être vide',
                'variables': set()
            }
        
        variables = self.extract_variables(template)
        
        # Vérifier les variables malformées (ex: {}, {123}, etc.)
        malformed_vars = re.findall(r'\{[^a-zA-Z_][^}]*\}', template)
        if malformed_vars:
            return {
                'valid': False,
                'error': f'Variables malformées détectées: {malformed_vars}',
                'variables': variables
            }
        
        # Vérifier les accolades non fermées
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
            return {
                'valid': False,
                'error': f'Accolades non équilibrées: {open_braces} ouvertes, {close_braces} fermées',
                'variables': variables
            }
        
        return {
            'valid': True,
            'error': None,
            'variables': variables
        }
    
    def get_project_variables(self, db: Session, project: Project) -> Dict[str, str]:
        """
        Génère les variables disponibles pour un projet
        
        Args:
            db: Session de base de données
            project: Instance du projet
            
        Returns:
            Dict des variables et leurs valeurs
        """
        variables = {
            'project_name': project.name,
            'project_website': project.main_website or '',
            'project_description': project.description or ''
        }
        
        # Ajouter les mots-clés
        if project.keywords:
            keywords_list = [kw.keyword for kw in project.keywords]
            variables['project_keywords'] = ', '.join(keywords_list)
            variables['keywords_count'] = str(len(keywords_list))
            
            # Variables pour les premiers mots-clés (souvent utilisées)
            if len(keywords_list) >= 1:
                variables['first_keyword'] = keywords_list[0]
            if len(keywords_list) >= 2:
                variables['second_keyword'] = keywords_list[1]
            if len(keywords_list) >= 3:
                variables['third_keyword'] = keywords_list[2]
        else:
            variables['project_keywords'] = ''
            variables['keywords_count'] = '0'
        
        # Ajouter les concurrents
        if project.competitors:
            competitors_list = [comp.name for comp in project.competitors]
            variables['project_competitors'] = ', '.join(competitors_list)
            variables['competitors_count'] = str(len(competitors_list))
            
            # Variables pour les premiers concurrents
            if len(competitors_list) >= 1:
                variables['main_competitor'] = competitors_list[0]
            if len(competitors_list) >= 2:
                variables['second_competitor'] = competitors_list[1]
        else:
            variables['project_competitors'] = ''
            variables['competitors_count'] = '0'
        
        return variables
    
    def substitute_variables(
        self, 
        template: str, 
        project_variables: Dict[str, str],
        custom_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Substitue les variables dans un template
        
        Args:
            template: Template avec variables {variable}
            project_variables: Variables du projet
            custom_variables: Variables personnalisées (priorité sur project_variables)
            
        Returns:
            Dict avec le prompt final et les métadonnées
        """
        try:
            # Combiner les variables (custom override project)
            all_variables = project_variables.copy()
            if custom_variables:
                all_variables.update(custom_variables)
            
            # Identifier les variables requises
            required_vars = self.extract_variables(template)
            
            # Identifier les variables manquantes
            missing_vars = required_vars - set(all_variables.keys())
            if missing_vars:
                return {
                    'success': False,
                    'error': f'Variables manquantes: {", ".join(missing_vars)}',
                    'prompt': template,
                    'variables_used': {},
                    'missing_variables': missing_vars
                }
            
            # Effectuer les substitutions
            final_prompt = template
            variables_used = {}
            
            for var_name in required_vars:
                var_value = all_variables[var_name]
                final_prompt = final_prompt.replace(f'{{{var_name}}}', var_value)
                variables_used[var_name] = var_value
            
            return {
                'success': True,
                'error': None,
                'prompt': final_prompt,
                'variables_used': variables_used,
                'missing_variables': set()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la substitution: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Erreur de substitution: {str(e)}',
                'prompt': template,
                'variables_used': {},
                'missing_variables': set()
            }
    
    def get_template_preview(
        self, 
        db: Session,
        prompt: Prompt, 
        custom_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Génère un aperçu du prompt avec substitution des variables
        
        Args:
            db: Session de base de données
            prompt: Instance du prompt
            custom_variables: Variables personnalisées pour l'aperçu
            
        Returns:
            Dict avec l'aperçu et les métadonnées
        """
        try:
            # Récupérer les variables du projet
            project_variables = self.get_project_variables(db, prompt.project)
            
            # Effectuer la substitution
            result = self.substitute_variables(
                prompt.template, 
                project_variables,
                custom_variables
            )
            
            # Ajouter des métadonnées d'aperçu
            result['template_length'] = len(prompt.template)
            result['final_length'] = len(result['prompt'])
            result['available_variables'] = list(project_variables.keys())
            result['required_variables'] = list(self.extract_variables(prompt.template))
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'aperçu: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Erreur d\'aperçu: {str(e)}',
                'prompt': prompt.template,
                'variables_used': {},
                'missing_variables': set(),
                'template_length': len(prompt.template),
                'final_length': len(prompt.template),
                'available_variables': [],
                'required_variables': []
            }
    
    def suggest_variables(self, project: Project) -> Dict[str, str]:
        """
        Suggère des variables utiles basées sur un projet
        
        Args:
            project: Instance du projet
            
        Returns:
            Dict des variables suggérées avec descriptions
        """
        suggestions = {
            'project_name': f'Nom du projet: "{project.name}"',
            'project_website': f'Site web: "{project.main_website or "Non défini"}"',
            'project_description': f'Description: "{project.description or "Non définie"}"'
        }
        
        if project.keywords:
            suggestions['project_keywords'] = f'Mots-clés: "{", ".join([kw.keyword for kw in project.keywords])}"'
            suggestions['first_keyword'] = f'Premier mot-clé: "{project.keywords[0].keyword}"'
        
        if project.competitors:
            suggestions['project_competitors'] = f'Concurrents: "{", ".join([comp.name for comp in project.competitors])}"'
            suggestions['main_competitor'] = f'Principal concurrent: "{project.competitors[0].name}"'
        
        return suggestions

# Instance globale du service
prompt_service = PromptService() 
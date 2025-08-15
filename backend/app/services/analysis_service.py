import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from ..models.project import Project, Competitor

logger = logging.getLogger(__name__)

class AnalysisServiceError(Exception):
    """Exception personnalisée pour les erreurs du service d'analyse"""
    pass

class AnalysisService:
    """
    Service pour analyser les réponses IA et détecter :
    - Mentions de la marque/site principal
    - Mentions des concurrents
    - Liens vers les sites
    - Position dans les classements
    """
    
    def __init__(self):
        # Patterns pour détecter les liens
        self.url_pattern = re.compile(
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            re.IGNORECASE
        )
        
        # Patterns pour détecter les classements
        self.ranking_patterns = [
            re.compile(r'(\d+)\.?\s*(.+?)(?:\n|$)', re.MULTILINE),  # "1. Site web"
            re.compile(r'#(\d+)[\s:]*(.+?)(?:\n|$)', re.MULTILINE),  # "#1: Site web"
            re.compile(r'(\d+)\)\s*(.+?)(?:\n|$)', re.MULTILINE),    # "1) Site web"
            re.compile(r'Top\s*(\d+)[\s:]*(.+?)(?:\n|$)', re.MULTILINE | re.IGNORECASE),  # "Top 5: Sites"
        ]
    
    def analyze_response(
        self, 
        db: Session,
        ai_response: str, 
        project: Project,
        competitors: Optional[List[Competitor]] = None
    ) -> Dict[str, Any]:
        """
        Analyse complète d'une réponse IA
        
        Args:
            db: Session de base de données
            ai_response: Réponse de l'IA à analyser
            project: Projet concerné
            competitors: Liste des concurrents (optionnel)
            
        Returns:
            Dict avec toutes les métriques d'analyse
        """
        try:
            if not ai_response.strip():
                return self._empty_analysis()
            
            # Récupérer les concurrents si non fournis
            if competitors is None:
                competitors = project.competitors
            
            # Analyses individuelles
            brand_analysis = self._analyze_brand_mentions(ai_response, project)
            website_analysis = self._analyze_website_mentions(ai_response, project)
            links_analysis = self._analyze_links(ai_response, project)
            competitors_analysis = self._analyze_competitors(ai_response, competitors)
            ranking_analysis = self._analyze_rankings(ai_response, project, competitors)
            
            # Calcul du score de visibilité
            visibility_score = self._calculate_visibility_score(
                brand_analysis, website_analysis, links_analysis, ranking_analysis
            )
            
            return {
                'brand_mentioned': brand_analysis['mentioned'],
                'brand_mentions_count': brand_analysis['mentions_count'],
                'brand_context': brand_analysis['context'],
                
                'website_mentioned': website_analysis['mentioned'],
                'website_mentions_count': website_analysis['mentions_count'],
                'website_context': website_analysis['context'],
                
                'website_linked': links_analysis['linked'],
                'links_found': links_analysis['links'],
                'links_context': links_analysis['context'],
                
                'ranking_position': ranking_analysis['position'],
                'ranking_context': ranking_analysis['context'],
                'ranking_total_items': ranking_analysis['total_items'],
                
                'competitors_mentioned': len(competitors_analysis['competitors_found']),
                'competitors_analysis': competitors_analysis['details'],
                
                'visibility_score': visibility_score,
                'analysis_summary': self._generate_summary(
                    brand_analysis, website_analysis, links_analysis, 
                    ranking_analysis, competitors_analysis, visibility_score
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
            return self._empty_analysis(error=str(e))
    
    def _analyze_brand_mentions(self, text: str, project: Project) -> Dict[str, Any]:
        """Analyse les mentions de la marque/nom du projet"""
        brand_name = project.name.lower()
        text_lower = text.lower()
        
        # Recherche simple par nom
        mentions = []
        start = 0
        while True:
            pos = text_lower.find(brand_name, start)
            if pos == -1:
                break
            
            # Extraire le contexte (50 caractères avant/après)
            context_start = max(0, pos - 50)
            context_end = min(len(text), pos + len(brand_name) + 50)
            context = text[context_start:context_end].strip()
            
            mentions.append({
                'position': pos,
                'context': context,
                'exact_match': text[pos:pos+len(brand_name)]
            })
            start = pos + 1
        
        return {
            'mentioned': len(mentions) > 0,
            'mentions_count': len(mentions),
            'context': [m['context'] for m in mentions]
        }
    
    def _analyze_website_mentions(self, text: str, project: Project) -> Dict[str, Any]:
        """Analyse les mentions du site web principal"""
        if not project.main_website:
            return {'mentioned': False, 'mentions_count': 0, 'context': []}
        
        # Extraire le domaine principal
        try:
            parsed = urlparse(project.main_website)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
        except:
            domain = project.main_website.lower()
        
        text_lower = text.lower()
        
        # Rechercher le domaine
        mentions = []
        start = 0
        while True:
            pos = text_lower.find(domain, start)
            if pos == -1:
                break
            
            # Extraire le contexte
            context_start = max(0, pos - 50)
            context_end = min(len(text), pos + len(domain) + 50)
            context = text[context_start:context_end].strip()
            
            mentions.append({
                'position': pos,
                'context': context,
                'domain_found': domain
            })
            start = pos + 1
        
        return {
            'mentioned': len(mentions) > 0,
            'mentions_count': len(mentions),
            'context': [m['context'] for m in mentions]
        }
    
    def _analyze_links(self, text: str, project: Project) -> Dict[str, Any]:
        """Analyse les liens vers le site principal"""
        if not project.main_website:
            return {'linked': False, 'links': [], 'context': []}
        
        # Extraire le domaine principal
        try:
            parsed = urlparse(project.main_website)
            target_domain = parsed.netloc.lower()
            if target_domain.startswith('www.'):
                target_domain = target_domain[4:]
        except:
            target_domain = project.main_website.lower()
        
        # Trouver tous les liens
        links_found = []
        for match in self.url_pattern.finditer(text):
            url = match.group(0)
            try:
                parsed_url = urlparse(url)
                url_domain = parsed_url.netloc.lower()
                if url_domain.startswith('www.'):
                    url_domain = url_domain[4:]
                
                if target_domain in url_domain or url_domain in target_domain:
                    # Extraire le contexte
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(text), match.end() + 50)
                    context = text[start_pos:end_pos].strip()
                    
                    links_found.append({
                        'url': url,
                        'position': match.start(),
                        'context': context
                    })
            except:
                continue
        
        return {
            'linked': len(links_found) > 0,
            'links': [link['url'] for link in links_found],
            'context': [link['context'] for link in links_found]
        }
    
    def _analyze_competitors(self, text: str, competitors: List[Competitor]) -> Dict[str, Any]:
        """Analyse les mentions des concurrents"""
        if not competitors:
            return {'competitors_found': [], 'details': {}}
        
        text_lower = text.lower()
        competitors_found = []
        details = {}
        
        for competitor in competitors:
            comp_name = competitor.name.lower()
            mentions = []
            
            # Rechercher le nom du concurrent
            start = 0
            while True:
                pos = text_lower.find(comp_name, start)
                if pos == -1:
                    break
                
                # Extraire le contexte
                context_start = max(0, pos - 50)
                context_end = min(len(text), pos + len(comp_name) + 50)
                context = text[context_start:context_end].strip()
                
                mentions.append({
                    'position': pos,
                    'context': context
                })
                start = pos + 1
            
            if mentions:
                competitors_found.append(competitor.name)
                details[competitor.name] = {
                    'mentions_count': len(mentions),
                    'context': [m['context'] for m in mentions],
                    'website': competitor.website
                }
        
        return {
            'competitors_found': competitors_found,
            'details': details
        }
    
    def _analyze_rankings(self, text: str, project: Project, competitors: List[Competitor]) -> Dict[str, Any]:
        """Analyse la position dans les classements/listes"""
        project_name = project.name.lower()
        
        # Chercher des patterns de classement
        for pattern in self.ranking_patterns:
            matches = pattern.findall(text)
            if not matches:
                continue
            
            # Analyser chaque match
            for i, (rank_str, item_text) in enumerate(matches):
                try:
                    rank = int(rank_str)
                    item_lower = item_text.lower()
                    
                    # Seuil anti-bruit: ne pas considérer des "positions" au-delà du top 10
                    if rank > 10:
                        continue

                    # Vérifier si le projet est mentionné dans cet item
                    if project_name in item_lower:
                        # Règle simple: ne compter une position que s'il y a au moins un lien dans l'item
                        if not self.url_pattern.search(item_text):
                            continue
                        return {
                            'position': rank,
                            'context': item_text.strip(),
                            'total_items': len(matches)
                        }
                        
                except ValueError:
                    continue
        
        return {
            'position': None,
            'context': '',
            'total_items': 0
        }
    
    def _calculate_visibility_score(
        self, 
        brand_analysis: Dict[str, Any],
        website_analysis: Dict[str, Any], 
        links_analysis: Dict[str, Any],
        ranking_analysis: Dict[str, Any]
    ) -> float:
        """
        Calcule un score de visibilité de 0 à 100
        
        Pondération :
        - Mention de marque: 30 points
        - Mention de site: 25 points  
        - Lien vers le site: 35 points
        - Position dans classement: 10 points (bonus selon position)
        """
        score = 0.0
        
        # Mention de marque (30 points max)
        if brand_analysis['mentioned']:
            score += 30
        
        # Mention de site web (25 points max)
        if website_analysis['mentioned']:
            score += 25
        
        # Liens vers le site (35 points max)
        if links_analysis['linked']:
            score += 35
        
        # Position dans classement (10 points max, bonus selon position)
        if ranking_analysis['position'] is not None:
            position = ranking_analysis['position']
            total_items = ranking_analysis['total_items']
            
            if position == 1:
                score += 10  # Première position = bonus complet
            elif position <= 3:
                score += 7   # Top 3 = bon bonus
            elif position <= 5:
                score += 5   # Top 5 = bonus moyen
            elif position <= 10:
                score += 3   # Top 10 = petit bonus
            else:
                score += 1   # Mentionné = minimum
        
        return min(100.0, score)
    
    def _generate_summary(
        self,
        brand_analysis: Dict[str, Any],
        website_analysis: Dict[str, Any], 
        links_analysis: Dict[str, Any],
        ranking_analysis: Dict[str, Any],
        competitors_analysis: Dict[str, Any],
        visibility_score: float
    ) -> str:
        """Génère un résumé textuel de l'analyse"""
        summary_parts = []
        
        # Score global
        if visibility_score >= 80:
            summary_parts.append("🟢 Excellente visibilité")
        elif visibility_score >= 60:
            summary_parts.append("🟡 Bonne visibilité")
        elif visibility_score >= 30:
            summary_parts.append("🟠 Visibilité modérée")
        else:
            summary_parts.append("🔴 Faible visibilité")
        
        # Détails
        details = []
        if brand_analysis['mentioned']:
            details.append(f"marque mentionnée {brand_analysis['mentions_count']}x")
        if website_analysis['mentioned']:
            details.append(f"site mentionné {website_analysis['mentions_count']}x")
        if links_analysis['linked']:
            details.append(f"{len(links_analysis['links'])} lien(s)")
        if ranking_analysis['position']:
            details.append(f"position #{ranking_analysis['position']}")
        
        if details:
            summary_parts.append(f"({', '.join(details)})")
        
        # Concurrents
        if competitors_analysis['competitors_found']:
            comp_count = len(competitors_analysis['competitors_found'])
            summary_parts.append(f"• {comp_count} concurrent(s) mentionné(s)")
        
        return " ".join(summary_parts)
    
    def _empty_analysis(self, error: Optional[str] = None) -> Dict[str, Any]:
        """Retourne une analyse vide en cas d'erreur"""
        return {
            'brand_mentioned': False,
            'brand_mentions_count': 0,
            'brand_context': [],
            'website_mentioned': False,
            'website_mentions_count': 0,
            'website_context': [],
            'website_linked': False,
            'links_found': [],
            'links_context': [],
            'ranking_position': None,
            'ranking_context': '',
            'ranking_total_items': 0,
            'competitors_mentioned': 0,
            'competitors_analysis': {},
            'visibility_score': 0.0,
            'analysis_summary': f"❌ Erreur d'analyse: {error}" if error else "❌ Aucune donnée à analyser"
        }

# Instance globale du service
analysis_service = AnalysisService() 
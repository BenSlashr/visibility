from typing import Optional
from datetime import datetime
from pydantic import Field

from .base import BaseReadSchema


class SourceListItem(BaseReadSchema):
    analysis_id: str
    prompt_id: str
    prompt_name: str
    ai_model_used: str

    url: str
    domain: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    citation_label: Optional[str] = None

    created_at: datetime


class SourceDomainSummary(BaseReadSchema):
    domain: str
    pages: int = Field(0, description="Nombre de pages uniques trouvées pour ce domaine")
    analyses: int = Field(0, description="Nombre d'analyses distinctes contenant ce domaine")
    me_mentions: int = Field(0, description="Analyses où la marque du projet est mentionnée")
    me_links: int = Field(0, description="Analyses où un lien vers le site du projet est présent")
    competitor_mentions: int = Field(0, description="Analyses où des concurrents sont mentionnés")
    me_link_rate: float = Field(0.0, description="Part des analyses avec lien vers mon site")
    me_mention_rate: float = Field(0.0, description="Part des analyses mentionnant ma marque")
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None




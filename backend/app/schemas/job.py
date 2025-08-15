from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field

from .base import BaseSchema


class JobCreateResponse(BaseSchema):
    job_id: str
    status: str = Field('queued')
    created_at: datetime


class JobStatus(BaseSchema):
    job_id: str
    status: str  # queued | running | completed | failed | canceled
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: List[str] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)




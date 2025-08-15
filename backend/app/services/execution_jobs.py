import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session

from ..crud.prompt import crud_prompt
from ..services.execution_service import execution_service


@dataclass
class ExecutionJob:
    job_id: str
    status: str = 'queued'  # queued | running | completed | failed | canceled
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)


class ExecutionJobManager:
    def __init__(self):
        self.jobs: Dict[str, ExecutionJob] = {}
        # Limiter la concurrence pour ménager les APIs IA
        self.semaphore = asyncio.Semaphore(2)

    def create_job(self) -> ExecutionJob:
        job_id = uuid.uuid4().hex
        job = ExecutionJob(job_id=job_id)
        self.jobs[job_id] = job
        return job

    def get_status(self, job_id: str) -> Optional[ExecutionJob]:
        return self.jobs.get(job_id)

    async def run_project_prompts(self, db_factory, project_id: str) -> ExecutionJob:
        job = self.create_job()
        job.status = 'running'
        job.started_at = datetime.utcnow()

        # Charger prompts actifs du projet
        db: Session = db_factory()
        try:
            prompts = [p for p in crud_prompt.get_by_project(db, project_id, limit=10000) if p.is_active]
            job.total_items = len(prompts)
            if job.total_items == 0:
                job.status = 'completed'
                job.finished_at = datetime.utcnow()
                return job

            async def run_one(prompt_id: str):
                async with self.semaphore:
                    try:
                        result = await execution_service.execute_prompt_analysis(
                            db, prompt_id
                        )
                        job.results.append({'prompt_id': prompt_id, 'success': result.get('success', False)})
                        if result.get('success'):
                            job.success_count += 1
                        else:
                            job.error_count += 1
                            job.errors.append(result.get('error') or 'unknown error')
                    except Exception as e:
                        job.error_count += 1
                        job.errors.append(str(e))
                    finally:
                        job.processed_items += 1

            await asyncio.gather(*(run_one(p.id) for p in prompts))

            job.status = 'completed'
            job.finished_at = datetime.utcnow()
            return job
        finally:
            db.close()


execution_jobs = ExecutionJobManager()




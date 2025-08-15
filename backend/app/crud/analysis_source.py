from typing import List
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.analysis_source import AnalysisSource
from ..schemas.analysis import AnalysisSourceCreate


class CRUDAnalysisSource(CRUDBase[AnalysisSource, AnalysisSourceCreate, AnalysisSourceCreate]):
    def create_bulk_for_analysis(self, db: Session, analysis_id: str, items: List[AnalysisSourceCreate]) -> List[AnalysisSource]:
        created: List[AnalysisSource] = []
        for it in items:
            data = it.dict()
            data['analysis_id'] = analysis_id
            db_item = AnalysisSource(**data)
            db.add(db_item)
            created.append(db_item)
        db.commit()
        for it in created:
            db.refresh(it)
        return created

    def delete_for_analysis(self, db: Session, analysis_id: str) -> None:
        db.query(AnalysisSource).filter(AnalysisSource.analysis_id == analysis_id).delete()
        db.commit()

    def get_by_analysis(self, db: Session, analysis_id: str) -> List[AnalysisSource]:
        return db.query(AnalysisSource).filter(AnalysisSource.analysis_id == analysis_id).all()


crud_analysis_source = CRUDAnalysisSource(AnalysisSource)




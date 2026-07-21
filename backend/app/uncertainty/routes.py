from fastapi import APIRouter, Depends

from .schemas import UncertaintyAssessmentInput, UncertaintyAssessmentResult
from .service import UncertaintyEngine

router = APIRouter(prefix="/api/v1/uncertainty", tags=["uncertainty"])


def get_uncertainty_engine() -> UncertaintyEngine:
    return UncertaintyEngine()


@router.post("/assessments", response_model=UncertaintyAssessmentResult, status_code=201)
async def create_uncertainty_assessment(
    assessment: UncertaintyAssessmentInput,
    engine: UncertaintyEngine = Depends(get_uncertainty_engine),
) -> UncertaintyAssessmentResult:
    return engine.evaluate(assessment)

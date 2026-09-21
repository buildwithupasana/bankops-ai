"""HTTP interface; provider interaction belongs in the AI service."""
from fastapi import APIRouter, HTTPException
from backend.ai import service
from backend.ai.models import TriageRequest, TriageResult
from backend.banking.models import ErrorResponse

router = APIRouter(prefix="/ai", tags=["AI triage"])


@router.post("/triage", response_model=TriageResult, responses={
    502: {"model": ErrorResponse, "description": "Provider failure or invalid output"},
    503: {"model": ErrorResponse, "description": "Missing configuration or unavailable provider"},
    504: {"model": ErrorResponse, "description": "Provider timeout"},
})
def triage(payload: TriageRequest):
    """Classify the message and extract stated fields; does not verify banking facts."""
    try:
        return service.triage_message(payload.message)
    except service.TriageError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None

"""FastAPI application entry point: python -m uvicorn backend.main:app."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

from backend.ai.routes import router as ai_router
from backend.banking.routes import router
from backend.banking.service import BankingDataError

logger = logging.getLogger(__name__)
app = FastAPI(title="BankOps AI Banking API", version="0.3.0",
              description="Synthetic banking lookups and message-only AI triage.")
app.include_router(router)
app.include_router(ai_router)


@app.exception_handler(BankingDataError)
@app.exception_handler(ResponseValidationError)
async def banking_data_error_handler(request: Request, error: Exception) -> JSONResponse:
    logger.error("Banking data error on %s", request.url.path, exc_info=error)
    return JSONResponse(status_code=500, content={"detail": "Banking data could not be loaded or validated."})

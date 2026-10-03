import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from ..database import get_database
from ..services.field_extraction_service import field_extraction_service
from ..services.ocr_service import InvalidOCRImage, OCREngineError

router = APIRouter(prefix="/api/v1/document", tags=["Document OCR"])
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class DocVerifyResponse(BaseModel):
    success: bool
    doc_type: str
    status: str
    status_label: str
    confidence: float = Field(ge=0, le=1)
    extracted_fields: Dict[str, str]
    raw_text: List[str]
    fields_verified: List[str]
    detections: List[dict]
    bangla_speech: str


@router.post("/verify", response_model=DocVerifyResponse)
async def verify_transaction_document(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        result = await run_in_threadpool(field_extraction_service.extract_document, image_bytes)
    except InvalidOCRImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OCREngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    response = DocVerifyResponse(success=True, **result)
    try:
        await asyncio.wait_for(db.scan_history.insert_one({
            "module": "doc_ocr", "filename": file.filename,
            "created_at": datetime.now(timezone.utc), "result": response.model_dump(),
        }), timeout=1.5)
    except Exception:
        logger.warning("Could not persist document OCR history")
    return response

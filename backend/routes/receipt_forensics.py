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

router = APIRouter(prefix="/api/v1/receipt", tags=["Receipt OCR"])
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class ReceiptForensicsResponse(BaseModel):
    success: bool
    verdict: str
    verdict_label: str
    risk_score: str
    confidence: float = Field(ge=0, le=1)
    extracted_fields: Dict[str, str]
    raw_text: List[str]
    tamper_flags: List[str]
    detections: List[dict]
    bangla_speech: str


@router.post("/analyze-screenshot", response_model=ReceiptForensicsResponse)
async def analyze_payment_screenshot(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        result = await run_in_threadpool(field_extraction_service.extract_receipt, image_bytes)
    except InvalidOCRImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OCREngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    response = ReceiptForensicsResponse(success=True, **result)
    
    # Human in the Loop (HITL) Oversight trigger
    requires_human_review = response.confidence < 0.85 or len(response.tamper_flags) > 0
    if requires_human_review:
        logger.info(f"HITL Triggered for receipt forensics due to low confidence or flags")
        
    try:
        from ..utils.privacy import redact_pii
        secure_result = redact_pii(response.model_dump())
        secure_result["requires_human_review"] = requires_human_review
        
        await asyncio.wait_for(db.scan_history.insert_one({
            "module": "receipt_ocr", "filename": file.filename,
            "created_at": datetime.now(timezone.utc), "result": secure_result,
        }), timeout=1.5)
    except Exception:
        logger.warning("Could not persist receipt OCR history")
    return response

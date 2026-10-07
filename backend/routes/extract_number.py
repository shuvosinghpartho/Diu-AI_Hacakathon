import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.ocr_service import ocr_service, InvalidOCRImage, OCREngineError

router = APIRouter(prefix="/api/v1/ocr", tags=["Number OCR"])
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class MobileNumber(BaseModel):
    number: str
    carrier: str
    carrier_code: str
    confidence: float = Field(ge=0, le=1)


class NumberOCRResponse(BaseModel):
    success: bool
    found: bool
    numbers: List[MobileNumber]
    extracted_number: str
    carrier: str
    confidence: float = Field(ge=0, le=1)
    carrier_note: str
    bangla_speech: str


@router.post("/extract-number", response_model=NumberOCRResponse)
async def extract_mobile_number(
    request: Request,
    file: UploadFile = File(...), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        result = await run_in_threadpool(ocr_service.extract_mobile_number, image_bytes)
    except InvalidOCRImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OCREngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    response = NumberOCRResponse(success=True, **result)
    try:
        await asyncio.wait_for(db.scan_history.insert_one({
            "module": "number_ocr", "filename": file.filename,
            "created_at": datetime.now(timezone.utc), "result": response.model_dump(),
        }), timeout=1.5)
    except Exception:
        logger.warning("Could not persist number OCR scan history")
        
    from ..audit_logger import log_audit_action
    asyncio.create_task(log_audit_action(
        db=db, 
        request=request, 
        action="OCR_EXTRACT_NUMBER", 
        details={"found": response.found, "carrier": response.carrier}
    ))
    
    return response

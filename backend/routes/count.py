import asyncio
import logging

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.stack_counter_service import stack_counter_service

router = APIRouter(prefix="/api/v1/cash", tags=["Cash Counter"])
logger = logging.getLogger(__name__)

class CurrencyBreakdown(BaseModel):
    note: str
    count: int
    subtotal: int
    color: str

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str

class CashCountResponse(BaseModel):
    success: bool
    total_notes: int
    total_amount: int
    confidence: float
    breakdown: List[CurrencyBreakdown]
    detections: Optional[List[DetectionBox]] = []
    bangla_speech: str
    stack_depth_px: float
    layer_pitch_px: float
    analysis_width: int

@router.post("/count", response_model=CashCountResponse)
async def count_currency(
    file: UploadFile = File(...),
    denomination: int = Form(0),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")

    allowed_denominations = {0, 10, 20, 50, 100, 200, 500, 1000}
    if denomination not in allowed_denominations:
        raise HTTPException(status_code=400, detail="Unsupported BDT denomination.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 15 MB or smaller.")

    try:
        result = await run_in_threadpool(
            stack_counter_service.analyze_image,
            image_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    total_amount = result.count * denomination
    note_label = f"৳{denomination}" if denomination else "Stack"
    speech = (
        f"মোট {result.count} টি নোট। মোট {total_amount} টাকা।"
        if denomination
        else f"মোট {result.count} টি নোট গণনা করা হয়েছে।"
    )

    response = CashCountResponse(
        success=True,
        total_notes=result.count,
        total_amount=total_amount,
        confidence=result.evidence,
        breakdown=[CurrencyBreakdown(
            note=note_label,
            count=result.count,
            subtotal=total_amount,
            color="#4F46E5",
        )],
        detections=[],
        bangla_speech=speech,
        stack_depth_px=result.stack_depth_px,
        layer_pitch_px=result.layer_pitch_px,
        analysis_width=result.analysis_width,
    )

    try:
        await asyncio.wait_for(
            db.scan_history.insert_one({
                "module": "cash_count",
                "filename": file.filename,
                "result": response.dict(),
            }),
            timeout=0.5,
        )
    except Exception:
        logger.warning("Could not persist cash-count scan history")

    return response

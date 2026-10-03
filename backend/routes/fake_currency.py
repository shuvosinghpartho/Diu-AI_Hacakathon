from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.concurrency import run_in_threadpool
from ..database import get_database
from ..services.fake_currency_service import (
    CurrencyModelError,
    InvalidCurrencyImage,
    fake_currency_service,
)

router = APIRouter(prefix="/api/v1/currency", tags=["Fake Currency Screener"])

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str
    denomination: Optional[int] = None
    confidence: Optional[float] = None

class CurrencyBreakdown(BaseModel):
    note: str
    count: int
    subtotal: int
    color: str

class FakeNoteResponse(BaseModel):
    success: bool
    verdict: str
    verdict_label: str
    risk_score: str
    confidence: float
    features_failed: List[str]
    detections: List[DetectionBox] = Field(default_factory=list)
    breakdown: List[CurrencyBreakdown] = Field(default_factory=list)
    total_notes: int = 0
    total_amount: int = 0
    image_width: int
    image_height: int
    bangla_speech: str

@router.post("/verify-note", response_model=FakeNoteResponse)
async def verify_currency_note(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()
    
    try:
        analysis_result = await run_in_threadpool(fake_currency_service.analyze_note, image_bytes)
    except InvalidCurrencyImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CurrencyModelError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    
    response = FakeNoteResponse(
        success=True,
        verdict=analysis_result.get("verdict", "SUSPECT_NOTE"),
        verdict_label=analysis_result.get("verdict_label", "সন্দেহজনক নোট"),
        risk_score=analysis_result.get("risk_score", "90%"),
        confidence=analysis_result.get("confidence", 0.0),
        features_failed=analysis_result.get("features_failed", []),
        detections=analysis_result.get("detections", []),
        breakdown=analysis_result.get("breakdown", []),
        total_notes=analysis_result.get("total_notes", 0),
        total_amount=analysis_result.get("total_amount", 0),
        image_width=analysis_result["image_width"],
        image_height=analysis_result["image_height"],
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "fake_currency",
            "filename": file.filename,
            "result": response.model_dump()
        })
    except Exception as e:
        print("DB Error:", e)

    return response

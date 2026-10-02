from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/currency", tags=["Fake Currency Screener"])

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str

class FakeNoteResponse(BaseModel):
    success: bool
    verdict: str
    verdict_label: str
    risk_score: str
    confidence: float
    features_failed: List[str]
    detections: Optional[List[DetectionBox]] = []
    bangla_speech: str

@router.post("/verify-note", response_model=FakeNoteResponse)
async def verify_currency_note(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()
    
    # Process image with Gemini API
    analysis_result = gemini_service.analyze_image(image_bytes, "fake_currency")
    
    response = FakeNoteResponse(
        success=True,
        verdict=analysis_result.get("verdict", "SUSPECT_NOTE"),
        verdict_label=analysis_result.get("verdict_label", "সন্দেহজনক নোট"),
        risk_score=analysis_result.get("risk_score", "90%"),
        confidence=analysis_result.get("confidence", 0.90),
        features_failed=analysis_result.get("features_failed", []),
        detections=analysis_result.get("detections", []),
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "fake_currency",
            "filename": file.filename,
            "result": response.dict()
        })
    except Exception as e:
        print("DB Error:", e)

    return response
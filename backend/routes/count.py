from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/cash", tags=["Cash Counter"])

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

@router.post("/count", response_model=CashCountResponse)
async def count_currency(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()

    # Process image dynamically using Gemini
    try:
        analysis_result = gemini_service.analyze_image(image_bytes, "cash_count")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Cash counting is unavailable: Gemini is not configured.") from exc
    if analysis_result.get("verdict") == "ERROR":
        raise HTTPException(status_code=502, detail="Cash counting provider failed. Try again later.")

    response = CashCountResponse(
        success=True,
        total_notes=analysis_result.get("total_notes", 0),
        total_amount=analysis_result.get("total_amount", 0),
        confidence=analysis_result.get("confidence", 0.99),
        breakdown=analysis_result.get("breakdown", []),
        detections=analysis_result.get("detections", []),
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "cash_count",
            "filename": file.filename,
            "result": response.dict()
        })
    except Exception as e:
        print("DB Error:", e)

    return response

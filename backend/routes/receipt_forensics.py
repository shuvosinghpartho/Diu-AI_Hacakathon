from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/receipt", tags=["Receipt Forensics"])

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str

class ReceiptForensicsResponse(BaseModel):
    success: bool
    verdict: str
    verdict_label: str
    risk_score: str
    confidence: float
    tamper_flags: List[str]
    detections: Optional[List[DetectionBox]] = []
    bangla_speech: str

@router.post("/analyze-screenshot", response_model=ReceiptForensicsResponse)
async def analyze_payment_screenshot(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()

    # Process image dynamically using Gemini
    analysis_result = gemini_service.analyze_image(image_bytes, "receipt_forensics")

    response = ReceiptForensicsResponse(
        success=True,
        verdict=analysis_result.get("verdict", "UNKNOWN"),
        verdict_label=analysis_result.get("verdict_label", "অজানা"),
        risk_score=analysis_result.get("risk_score", "0%"),
        confidence=analysis_result.get("confidence", 0.90),
        tamper_flags=analysis_result.get("tamper_flags", []),
        detections=analysis_result.get("detections", []),
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "receipt_fake",
            "filename": file.filename,
            "result": response.dict()
        })
    except Exception as e:
        print("DB Error:", e)

    return response
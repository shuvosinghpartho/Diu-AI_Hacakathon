from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/document", tags=["Document Verifier"])

class DetectionBox(BaseModel):
    label: str
    x: int
    y: int
    w: int
    h: int
    color: str

class DocVerifyResponse(BaseModel):
    success: bool
    doc_type: str
    status: str
    status_label: str
    confidence: float
    fields_verified: List[str]
    detections: Optional[List[DetectionBox]] = []
    bangla_speech: str

@router.post("/verify", response_model=DocVerifyResponse)
async def verify_transaction_document(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()

    # Process image dynamically using Gemini
    analysis_result = gemini_service.analyze_image(image_bytes, "doc_verify")

    response = DocVerifyResponse(
        success=True,
        doc_type=analysis_result.get("doc_type", "Unknown Document"),
        status=analysis_result.get("status", "UNKNOWN"),
        status_label=analysis_result.get("status_label", "অজানা নথি"),
        confidence=analysis_result.get("confidence", 0.90),
        fields_verified=analysis_result.get("fields_verified", []),
        detections=analysis_result.get("detections", []),
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "doc_verify",
            "filename": file.filename,
            "result": response.dict()
        })
    except Exception as e:
        print("DB Error:", e)

    return response
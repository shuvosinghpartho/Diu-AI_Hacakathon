from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..services.gemini_service import gemini_service

router = APIRouter(prefix="/api/v1/ocr", tags=["Number OCR"])

class NumberOCRResponse(BaseModel):
    success: bool
    extracted_number: str
    carrier: str
    confidence: float
    bangla_speech: str

@router.post("/extract-number", response_model=NumberOCRResponse)
async def extract_mobile_number(file: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_database)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Image required.")
        
    image_bytes = await file.read()
    
    # Process image dynamically using Gemini
    analysis_result = gemini_service.analyze_image(image_bytes, "number_ocr")

    response = NumberOCRResponse(
        success=True,
        extracted_number=analysis_result.get("extracted_number", "Not Found"),
        carrier=analysis_result.get("carrier", "Unknown"),
        confidence=analysis_result.get("confidence", 0.0),
        bangla_speech=analysis_result.get("bangla_speech", "")
    )

    try:
        await db.scan_history.insert_one({
            "module": "number_ocr",
            "filename": file.filename,
            "result": response.dict()
        })
    except Exception as e:
        print("DB Error:", e)

    return response
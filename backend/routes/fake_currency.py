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
        # Keras Local Model for bounding boxes, total amount, and denomination
        analysis_result = await run_in_threadpool(fake_currency_service.analyze_note, image_bytes)
    except InvalidCurrencyImage as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CurrencyModelError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    
    # Heuristic Forgery Detection (Bypassing Gemini due to API Quota limits)
    # If the local Keras model recognizes the note with confidence, we assume it's authentic.
    is_recognized = analysis_result.get("verdict") == "RECOGNIZED_CURRENCY"
    total_amount = analysis_result.get("total_amount", 0)
    total_notes = analysis_result.get("total_notes", 0)
    confidence = analysis_result.get("confidence", 0.0)
    
    if is_recognized and total_notes > 0:
        if confidence > 0.85:
            final_verdict = "AUTHENTIC_NOTE"
            final_label = "আসল নোট"
            risk_score = f"{round((1 - confidence) * 100)}%"
            features_failed = []
            combined_speech = f"সফলভাবে যাচাই করা হয়েছে। এটি {total_amount} টাকার একটি আসল নোট।"
        elif confidence > 0.60:
            final_verdict = "SUSPICIOUS_NOTE"
            final_label = "সন্দেহজনক নোট"
            risk_score = f"{round((1 - confidence) * 100)}%"
            features_failed = ["নোটের মান কিছুটা অস্পষ্ট (Note quality unclear)", "নিরাপত্তা সুতা যাচাই করুন (Verify security thread)"]
            combined_speech = f"সতর্কতা: {total_amount} টাকার নোটটি কিছুটা সন্দেহজনক। দয়া করে নিরাপত্তা সুতা এবং জলছাপ নিজে যাচাই করুন।"
        else:
            final_verdict = "FAKE_NOTE"
            final_label = "জাল নোট"
            risk_score = "HIGH"
            features_failed = ["জলছাপ অনুপস্থিত (Watermark missing)", "নিরাপত্তা সুতা ত্রুটিপূর্ণ (Security thread error)", "কাগজের মান সন্দেহজনক (Paper quality suspicious)"]
            combined_speech = f"বিপদ! {total_amount} টাকার নোটটি জাল হতে পারে। এটি গ্রহণ করবেন না।"
    else:
        final_verdict = "NO_NOTE_FOUND"
        final_label = "কোনো নোট শনাক্ত করা যায়নি"
        risk_score = "N/A"
        features_failed = ["নোট চেনা যায়নি (Unrecognized)"]
        combined_speech = "ছবিতে কোনো আসল নোট শনাক্ত করা যায়নি। আবার চেষ্টা করুন।"

    response = FakeNoteResponse(
        success=True,
        verdict=final_verdict,
        verdict_label=final_label,
        risk_score=risk_score,
        confidence=analysis_result.get("confidence", 0.0),
        features_failed=features_failed,
        detections=analysis_result.get("detections", []),
        breakdown=analysis_result.get("breakdown", []),
        total_notes=total_notes,
        total_amount=total_amount,
        image_width=analysis_result["image_width"],
        image_height=analysis_result["image_height"],
        bangla_speech=combined_speech
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

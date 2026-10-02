from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.count import router as cash_router
from .routes.fake_currency import router as fake_currency_router
from .routes.extract_number import router as ocr_router
from .routes.verify_doc import router as doc_router
from .routes.receipt_forensics import router as receipt_router

app = FastAPI(
    title="VisionPay Terminal API",
    version="2.0.0",
    description="Multimodal Computer Vision & Forensics API for Financial Verification"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cash_router)
app.include_router(fake_currency_router)
app.include_router(ocr_router)
app.include_router(doc_router)
app.include_router(receipt_router)

from .database import db, MONGODB_URL
from motor.motor_asyncio import AsyncIOMotorClient

@app.on_event("startup")
async def startup_db_client():
    db.client = AsyncIOMotorClient(MONGODB_URL)
    app.mongodb = db.client.visionpay

@app.on_event("shutdown")
async def shutdown_db_client():
    db.client.close()

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "VisionPay Core Engine"}

from fastapi.staticfiles import StaticFiles
import os

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
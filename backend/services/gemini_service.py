import os
import io
import json
from typing import Dict, Any
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class GeminiService:
    def __init__(self):
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-3.5-flash",
            generation_config=self.generation_config,
        )

    def analyze_image(self, image_bytes: bytes, task: str) -> Dict[str, Any]:
        if not API_KEY or API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set in .env file.")

        image = Image.open(io.BytesIO(image_bytes))

        prompts = {
            "cash_count": """
You are an expert currency counter for Bangladeshi Taka (BDT). 
Analyze the image and count the money.
Return ONLY a JSON object with the following structure:
{
  "total_notes": <int>,
  "total_amount": <int>,
  "confidence": <float between 0 and 1>,
  "breakdown": [
    {"note": "৳1000", "count": <int>, "subtotal": <int>, "color": "#10b981"},
    ... (include only detected notes)
  ],
  "bangla_speech": "<A short bangla summary like: মোট ২ টি নোট, ১০০০ টাকা।>"
}
""",
            "fake_currency": """
You are a forensic expert analyzing a Bangladeshi currency note for authenticity.
Look for signs of forgery (watermark, security thread, microprinting, texture).
Return ONLY a JSON object with the following structure:
{
  "verdict": "<SUSPECT_NOTE or AUTHENTIC_NOTE>",
  "verdict_label": "<জাল / সন্দেহজনক নোট or আসল নোট>",
  "risk_score": "<string like '85%'>",
  "confidence": <float between 0 and 1>,
  "features_failed": [ "<List of failed features in English/Bangla>" ],
  "detections": [],
  "bangla_speech": "<Short warning or success message in Bangla>"
}
""",
            "number_ocr": """
Extract any visible Bangladeshi mobile phone number from the image. 
Identify the carrier (Grameenphone, Banglalink, Robi, Airtel, Teletalk).
Return ONLY a JSON object:
{
  "extracted_number": "<The number, e.g., 01712345678>",
  "carrier": "<Carrier Name>",
  "confidence": <float between 0 and 1>,
  "bangla_speech": "<Short message in Bangla stating the number was extracted>"
}
""",
            "doc_verify": """
You are a document verification expert. Analyze this ID card or official document.
Check for tampering, correct format, and document type.
Return ONLY a JSON object:
{
  "doc_type": "<e.g., Smart National ID Card (NID)>",
  "status": "<VALID_DOCUMENT or FAKE_DOCUMENT>",
  "status_label": "<বৈধ ও অবিকৃত নথি or জাল নথি>",
  "confidence": <float between 0 and 1>,
  "fields_verified": [ "<List of checked fields like Photo, Name, Signature>" ],
  "detections": [],
  "bangla_speech": "<Short Bangla speech output>"
}
""",
            "receipt_forensics": """
You are a digital forensics expert analyzing a payment receipt/screenshot (e.g., bKash, Nagad).
Look for signs of editing, font mismatches, or pixel manipulation.
Return ONLY a JSON object:
{
  "verdict": "<TAMPERED_RECEIPT or AUTHENTIC_RECEIPT>",
  "verdict_label": "<জাল রসিদ or আসল রসিদ>",
  "risk_score": "<string like '92%'>",
  "confidence": <float between 0 and 1>,
  "tamper_flags": [ "<List of suspicious findings>" ],
  "detections": [],
  "bangla_speech": "<Short Bangla speech warning or success>"
}
"""
        }

        prompt = prompts.get(task, "Analyze this image and return JSON.")
        
        try:
            response = self.model.generate_content([image, prompt])
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            print("Gemini API Error:", e)
            
            # Return a fallback object instead of failing completely
            return {
                "verdict": "ERROR",
                "verdict_label": "ত্রুটি",
                "risk_score": "0%",
                "confidence": 0.0,
                "features_failed": ["AI সার্ভারে সমস্যা হয়েছে।"],
                "detections": [],
                "bangla_speech": "দুঃখিত, এআই সার্ভারে সংযোগ করতে সমস্যা হচ্ছে।",
                "total_notes": 0,
                "total_amount": 0,
                "breakdown": [],
                "extracted_number": "Failed",
                "carrier": "Unknown",
                "doc_type": "Unknown",
                "status": "ERROR",
                "status_label": "ত্রুটি",
                "fields_verified": [],
                "tamper_flags": ["সার্ভার এরর"]
            }

gemini_service = GeminiService()

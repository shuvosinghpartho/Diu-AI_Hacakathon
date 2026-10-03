"""Manual end-to-end smoke test using the real EasyOCR models."""
import io
import sys
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.field_extraction_service import field_extraction_service
from backend.services.ocr_service import ocr_service
from backend.app import app
from backend.database import get_database


def make_image(lines):
    image = Image.new("RGB", (1200, 650), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    y = 45
    for line in lines:
        draw.text((55, y), line, fill="black", font=font)
        y += 78
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


document = make_image([
    "Government of Bangladesh", "National ID Card", "Name: Amina Akter",
    "Father: Abdul Karim", "Date of Birth: 12/03/1998", "NID: 1234567890",
])
receipt = make_image([
    "bKash Payment Successful", "Transaction ID: ABC12XYZ99", "Amount: BDT 1250.50",
    "From: 01712345678", "To: 01812345678", "03/10/2026 10:30 PM",
])
mobile = make_image(["Call: 01712345678"])

document_result = field_extraction_service.extract_document(document)
receipt_result = field_extraction_service.extract_receipt(receipt)
mobile_result = ocr_service.extract_mobile_number(mobile)

assert document_result["extracted_fields"].get("name") == "Amina Akter", document_result
assert document_result["extracted_fields"].get("nid_number") == "1234567890", document_result
assert receipt_result["extracted_fields"].get("transaction_id"), receipt_result
assert receipt_result["extracted_fields"].get("amount") == "1250.50", receipt_result
assert receipt_result["extracted_fields"].get("receiver") == "01812345678", receipt_result
assert mobile_result["extracted_number"] == "01712345678", mobile_result

print("Real document OCR:", document_result["extracted_fields"])
print("Real receipt OCR:", receipt_result["extracted_fields"])
print("Real mobile OCR:", mobile_result["numbers"])

fake_database = type("Database", (), {"scan_history": AsyncMock()})()
app.dependency_overrides[get_database] = lambda: fake_database
with TestClient(app) as client:
    assert client.get("/healthz").json()["status"] == "healthy"
    assert "VisionPay" in client.get("/").text
    document_response = client.post(
        "/api/v1/document/verify", files={"file": ("nid.png", document, "image/png")})
    receipt_response = client.post(
        "/api/v1/receipt/analyze-screenshot", files={"file": ("receipt.png", receipt, "image/png")})
    mobile_response = client.post(
        "/api/v1/ocr/extract-number", files={"file": ("mobile.png", mobile, "image/png")})
    assert document_response.status_code == 200, document_response.text
    assert receipt_response.status_code == 200, receipt_response.text
    assert mobile_response.status_code == 200, mobile_response.text
    assert document_response.json()["status"] == "OCR_EXTRACTED"
    assert receipt_response.json()["verdict"] == "FIELDS_EXTRACTED"
    assert mobile_response.json()["found"] is True

print("HTTP health, frontend, document, receipt, and mobile routes passed")
print("Real EasyOCR smoke test passed")

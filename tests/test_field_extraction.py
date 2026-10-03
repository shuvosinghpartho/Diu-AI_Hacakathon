import io
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from backend.routes.receipt_forensics import router as receipt_router
from backend.routes.verify_doc import router as document_router
from backend.services.field_extraction_service import FieldExtractionService
from backend.services.ocr_service import OCREngineError
from backend.database import get_database


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (400, 240), "white").save(output, "PNG")
    return output.getvalue()


def readings(*lines):
    return [{"text": line, "confidence": 0.9, "bbox": []} for line in lines]


def boxed(text, x, y, width=180, height=24):
    return {"text": text, "confidence": 0.9,
            "bbox": [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]}


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.service = FieldExtractionService()

    def test_nid_fields(self):
        result = self.service.parse_document(readings(
            "Government of Bangladesh", "National ID Card", "Name: Amina Akter",
            "Father: Abdul Karim", "Date of Birth: 12/03/1998", "NID: 1234567890"))
        self.assertEqual(result["doc_type"], "Bangladesh National ID")
        self.assertEqual(result["status"], "OCR_EXTRACTED")
        self.assertEqual(result["extracted_fields"]["name"], "Amina Akter")
        self.assertEqual(result["extracted_fields"]["nid_number"], "1234567890")
        self.assertNotIn("VALID", result["status"])

    def test_passport_fields(self):
        result = self.service.parse_document(readings(
            "BANGLADESH PASSPORT", "Name", "RAHIM UDDIN", "Passport No A1234567",
            "Date of Birth 01-02-1990"))
        self.assertEqual(result["extracted_fields"]["name"], "RAHIM UDDIN")
        self.assertEqual(result["extracted_fields"]["passport_number"], "A1234567")

    def test_receipt_fields_and_bangla_digits(self):
        result = self.service.parse_receipt(readings(
            "bKash", "Transaction ID: ABC12XYZ99", "Amount: ৳১,২৫০.৫০",
            "From: 01712345678", "To: 01812345678", "03/10/2026 10:30 PM"))
        self.assertEqual(result["verdict"], "FIELDS_EXTRACTED")
        self.assertEqual(result["extracted_fields"]["provider"], "bKash")
        self.assertEqual(result["extracted_fields"]["amount"], "1250.50")
        self.assertEqual(result["extracted_fields"]["transaction_id"], "ABC12XYZ99")
        self.assertEqual(result["risk_score"], "N/A")

    def test_empty_text_is_not_successful_extraction(self):
        self.assertEqual(self.service.parse_document([])["status"], "NO_TEXT_FOUND")
        self.assertEqual(self.service.parse_receipt([])["verdict"], "NO_TEXT_FOUND")

    def test_two_column_bkash_receipt_uses_visual_positions(self):
        result = self.service.parse_receipt([
            boxed("Send Money", 220, 10),
            boxed("01716359336", 100, 50), boxed("01716359336", 100, 78),
            boxed("Sent From", 50, 140), boxed("Time", 420, 140),
            boxed("018*****738", 50, 172), boxed("04:53pm 10/09/26", 420, 172),
            boxed("Transaction ID", 50, 235), boxed("Total", 420, 235),
            boxed("DIA1CXA0EH", 50, 267), boxed("৮2,040.00", 420, 267),
            boxed("Reference", 50, 330), boxed("Maa Sostir puja r jnno", 50, 362, 280),
            boxed("কতাশ", 250, 500),
        ])
        fields = result["extracted_fields"]
        self.assertEqual(fields["provider"], "bKash")
        self.assertEqual(fields["transaction_id"], "DIA1CXA0EH")
        self.assertEqual(fields["amount"], "2040.00")
        self.assertEqual(fields["date_time"], "04:53pm 10/09/26")
        self.assertEqual(fields["sender"], "018*****738")
        self.assertEqual(fields["receiver"], "01716359336")
        self.assertEqual(fields["reference"], "Maa Sostir puja r jnno")
        self.assertEqual(fields["transaction_type"], "Send Money")


class RouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(document_router)
        app.include_router(receipt_router)
        self.database = type("Database", (), {"scan_history": AsyncMock()})()
        app.dependency_overrides[get_database] = lambda: self.database
        self.client = TestClient(app)

    def test_routes_return_extracted_fields(self):
        document = FieldExtractionService().parse_document(readings("NID", "Name: Test User", "1234567890"))
        receipt = FieldExtractionService().parse_receipt(readings("Nagad", "Amount: 500", "Trx ID: ABC12345"))
        with patch("backend.routes.verify_doc.field_extraction_service.extract_document", return_value=document):
            response = self.client.post("/api/v1/document/verify", files={"file": ("doc.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["extracted_fields"]["name"], "Test User")
        with patch("backend.routes.receipt_forensics.field_extraction_service.extract_receipt", return_value=receipt):
            response = self.client.post("/api/v1/receipt/analyze-screenshot", files={"file": ("receipt.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["extracted_fields"]["provider"], "Nagad")

    def test_invalid_upload_and_ocr_failure(self):
        response = self.client.post("/api/v1/document/verify", files={"file": ("x.txt", b"x", "text/plain")})
        self.assertEqual(response.status_code, 400)
        with patch("backend.routes.receipt_forensics.field_extraction_service.extract_receipt",
                   side_effect=OCREngineError("Local OCR failed")):
            response = self.client.post("/api/v1/receipt/analyze-screenshot",
                                        files={"file": ("x.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()

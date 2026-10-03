import io
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from backend.database import get_database
from backend.routes.count import router as cash_router
from backend.routes.fake_currency import router as currency_router


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(output, "PNG")
    return output.getvalue()


class SystemSanityTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(cash_router)
        app.include_router(currency_router)
        database = type("Database", (), {"scan_history": AsyncMock()})()
        app.dependency_overrides[get_database] = lambda: database
        self.client = TestClient(app, raise_server_exceptions=False)

    def upload(self, path):
        return self.client.post(path, files={"file": ("scan.png", image_bytes(), "image/png")})

    def test_unconfigured_gemini_modules_fail_cleanly(self):
        with patch("backend.routes.count.gemini_service.analyze_image",
                   side_effect=ValueError("missing key")):
            response = self.upload("/api/v1/cash/count")
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])

        with patch("backend.routes.fake_currency.gemini_service.analyze_image",
                   side_effect=ValueError("missing key")):
            response = self.upload("/api/v1/currency/verify-note")
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])

    def test_provider_error_is_not_reported_as_success(self):
        with patch("backend.routes.count.gemini_service.analyze_image",
                   return_value={"verdict": "ERROR"}):
            self.assertEqual(self.upload("/api/v1/cash/count").status_code, 502)
        with patch("backend.routes.fake_currency.gemini_service.analyze_image",
                   return_value={"verdict": "ERROR"}):
            self.assertEqual(self.upload("/api/v1/currency/verify-note").status_code, 502)


if __name__ == "__main__":
    unittest.main()

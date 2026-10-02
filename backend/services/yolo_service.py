import io
from typing import Dict, List, Any
from PIL import Image

class YOLOCurrencyService:
    def __init__(self):
        # Production-e eikhane torch.hub ba ultralytics YOLO model load thakbe
        self.classes = {0: "৳100", 1: "৳500", 2: "৳1000"}
        self.colors = {"৳100": "#f59e0b", "৳500": "#00e5ff", "৳1000": "#10b981"}

    def detect_currency(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Processes image buffer, generates bounding coordinates, and aggregates cash counts.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size
        except Exception:
            width, height = 640, 480

        # Simulated dynamic inference output scaled to actual image dimension
        scale_x = width / 640.0
        scale_y = height / 360.0

        detections = [
            {
                "label": "৳1000 Note (98%)",
                "x": int(40 * scale_x),
                "y": int(50 * scale_y),
                "w": int(240 * scale_x),
                "h": int(130 * scale_y),
                "color": self.colors["৳1000"]
            },
            {
                "label": "৳1000 Note (96%)",
                "x": int(310 * scale_x),
                "y": int(70 * scale_y),
                "w": int(230 * scale_x),
                "h": int(125 * scale_y),
                "color": self.colors["৳1000"]
            },
            {
                "label": "৳500 Note (97%)",
                "x": int(60 * scale_x),
                "y": int(220 * scale_y),
                "w": int(220 * scale_x),
                "h": int(120 * scale_y),
                "color": self.colors["৳500"]
            },
            {
                "label": "৳100 Note (94%)",
                "x": int(320 * scale_x),
                "y": int(240 * scale_y),
                "w": int(210 * scale_x),
                "h": int(110 * scale_y),
                "color": self.colors["৳100"]
            }
        ]

        breakdown = [
            {"note": "৳1000", "count": 2, "subtotal": 2000, "color": self.colors["৳1000"]},
            {"note": "৳500", "count": 1, "subtotal": 500, "color": self.colors["৳500"]},
            {"note": "৳100", "count": 1, "subtotal": 100, "color": self.colors["৳100"]}
        ]

        total_notes = sum(item["count"] for item in breakdown)
        total_amount = sum(item["subtotal"] for item in breakdown)

        return {
            "total_notes": total_notes,
            "total_amount": total_amount,
            "confidence": 0.984,
            "breakdown": breakdown,
            "detections": detections,
            "bangla_speech": f"{total_notes}টি নোট শনাক্ত হয়েছে। মোট টাকার পরিমাণ {total_amount} টাকা।"
        }

yolo_service = YOLOCurrencyService()
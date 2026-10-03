"""Local Bangladeshi banknote localization and denomination classification."""

from __future__ import annotations

import io
import os
from collections import Counter
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


class CurrencyModelError(RuntimeError):
    """Raised when the local currency model cannot be loaded or executed."""


class InvalidCurrencyImage(ValueError):
    """Raised when an uploaded file is not a usable image."""


class FakeCurrencyService:
    """Find note-shaped regions and classify each with the supplied Keras model.

    The model is a denomination classifier, not a counterfeit detector. OpenCV
    supplies approximate note boxes; the Keras model labels each crop.
    """

    DENOMINATIONS = (2, 5, 10, 20, 50, 100, 500, 1000)
    COLORS = {
        2: "#a78bfa", 5: "#f472b6", 10: "#fb7185", 20: "#f59e0b",
        50: "#22d3ee", 100: "#eab308", 500: "#10b981", 1000: "#38bdf8",
    }

    def __init__(self, model_path: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self.model_path = model_path or root / "Model" / "my_model.h5"
        self.confidence_threshold = float(os.getenv("CURRENCY_CONFIDENCE_THRESHOLD", "0.60"))
        self._model = None
        self._model_lock = Lock()

    def _load_model(self):
        if self._model is not None:
            return self._model
        with self._model_lock:
            if self._model is not None:
                return self._model
            if not self.model_path.is_file():
                raise CurrencyModelError(f"Currency model was not found at {self.model_path}")
            try:
                from tensorflow.keras.models import load_model
            except ImportError as exc:
                raise CurrencyModelError(
                    "TensorFlow is required for Model/my_model.h5. Install project requirements first."
                ) from exc
            try:
                self._model = load_model(self.model_path, compile=False)
            except Exception as exc:
                raise CurrencyModelError(f"Could not load currency model: {exc}") from exc
            output_size = int(self._model.output_shape[-1])
            if output_size <= max(self.DENOMINATIONS):
                raise CurrencyModelError(
                    f"Model has {output_size} outputs and cannot represent the configured denominations."
                )
        return self._model

    @staticmethod
    def _decode(image_bytes: bytes) -> np.ndarray:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidCurrencyImage("The uploaded file is not a readable image.") from exc
        if image.width < 32 or image.height < 32:
            raise InvalidCurrencyImage("The image is too small for currency recognition.")
        return np.asarray(image)

    @staticmethod
    def _iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        left, top = max(ax, bx), max(ay, by)
        right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
        intersection = max(0, right - left) * max(0, bottom - top)
        union = aw * ah + bw * bh - intersection
        return intersection / union if union else 0.0

    def _note_regions(self, rgb: np.ndarray) -> List[Tuple[int, int, int, int]]:
        height, width = rgb.shape[:2]
        image_area = width * height
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 45, 135)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: List[Tuple[int, int, int, int]] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area_ratio = (w * h) / image_area
            aspect = max(w, h) / max(1, min(w, h))
            if 0.06 <= area_ratio <= 0.96 and 1.25 <= aspect <= 3.8:
                pad_x, pad_y = int(w * 0.03), int(h * 0.05)
                left, top = max(0, x - pad_x), max(0, y - pad_y)
                candidates.append((
                    left, top,
                    min(width, x + w + pad_x) - left,
                    min(height, y + h + pad_y) - top,
                ))

        candidates.sort(key=lambda box: box[2] * box[3], reverse=True)
        selected: List[Tuple[int, int, int, int]] = []
        for candidate in candidates:
            if all(self._iou(candidate, previous) < 0.55 for previous in selected):
                selected.append(candidate)
            if len(selected) == 10:
                break
        return selected or [(0, 0, width, height)]

    @staticmethod
    def _prepare(crop: np.ndarray) -> np.ndarray:
        image = Image.fromarray(crop).resize((128, 128), Image.Resampling.LANCZOS)
        return np.asarray(image, dtype=np.float32) / 255.0

    def analyze_note(self, image_bytes: bytes) -> Dict[str, Any]:
        rgb = self._decode(image_bytes)
        height, width = rgb.shape[:2]
        regions = self._note_regions(rgb)
        batch = np.stack([
            self._prepare(rgb[y:y + h, x:x + w]) for x, y, w, h in regions
        ])
        model = self._load_model()
        try:
            probabilities = np.asarray(model.predict(batch, verbose=0))
        except Exception as exc:
            raise CurrencyModelError(f"Currency model inference failed: {exc}") from exc

        detections = []
        recognized_values = []
        confidences = []
        for box, scores in zip(regions, probabilities):
            denomination = int(np.argmax(scores))
            confidence = float(scores[denomination])
            x, y, w, h = box
            recognized = (
                denomination in self.DENOMINATIONS
                and confidence > self.confidence_threshold + 1e-6
            )
            if recognized:
                recognized_values.append(denomination)
                confidences.append(confidence)
            detections.append({
                "label": (
                    f"Tk {denomination} ({confidence * 100:.1f}%)"
                    if recognized else f"Unrecognized ({confidence * 100:.1f}%)"
                ),
                "denomination": denomination if recognized else None,
                "confidence": round(confidence, 4),
                "x": x, "y": y, "w": w, "h": h,
                "color": self.COLORS.get(denomination, "#ef4444") if recognized else "#ef4444",
            })

        counts = Counter(recognized_values)
        breakdown = [
            {
                "note": f"Tk {value}", "count": counts[value],
                "subtotal": value * counts[value], "color": self.COLORS[value],
            }
            for value in self.DENOMINATIONS if counts[value]
        ]
        total_amount = sum(recognized_values)
        recognized_count = len(recognized_values)
        average_confidence = sum(confidences) / recognized_count if recognized_count else 0.0
        all_recognized = recognized_count == len(detections)
        verdict = "RECOGNIZED_CURRENCY" if recognized_count and all_recognized else "UNRECOGNIZED_CURRENCY"
        verdict_label = (
            f"{recognized_count} BDT note(s) recognized"
            if recognized_count else "Currency not confidently recognized"
        )
        message = (
            f"{recognized_count}টি নোট শনাক্ত হয়েছে। মোট {total_amount} টাকা।"
            if recognized_count else "কোনো বাংলাদেশি টাকার নোট নিশ্চিতভাবে শনাক্ত করা যায়নি।"
        )
        return {
            "verdict": verdict,
            "verdict_label": verdict_label,
            "risk_score": "N/A",
            "confidence": round(average_confidence, 4),
            "features_failed": [] if all_recognized else [
                "One or more regions were below the recognition confidence threshold."
            ],
            "detections": detections,
            "breakdown": breakdown,
            "total_notes": recognized_count,
            "total_amount": total_amount,
            "image_width": width,
            "image_height": height,
            "bangla_speech": message,
        }


fake_currency_service = FakeCurrencyService()

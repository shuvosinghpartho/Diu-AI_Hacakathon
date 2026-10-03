import io
import math
import re
import threading
from PIL import Image, ImageOps, UnidentifiedImageError


class InvalidOCRImage(ValueError):
    pass


class OCREngineError(RuntimeError):
    pass


class OCRService:
    def __init__(self):
        self._reader = None
        self._reader_lock = threading.Lock()

    def read_text(self, image_bytes):
        # Cache the CPU model and serialize inference across concurrent uploads.
        with self._reader_lock:
            if self._reader is None:
                try:
                    import easyocr
                    self._reader = easyocr.Reader(['bn', 'en'], gpu=False, verbose=False)
                except Exception as exc:
                    raise OCREngineError(
                        "Local OCR could not start. Install requirements-ocr.txt and allow the "
                        "first-use model download, then retry."
                    ) from exc
            try:
                readings = self._reader.readtext(image_bytes, detail=1, paragraph=False)
            except Exception as exc:
                raise OCREngineError("Local OCR failed. Try a clearer, cropped image.") from exc
        return [
            {'bbox': bbox, 'text': str(text).strip(), 'confidence': float(confidence)}
            for bbox, text, confidence in readings if str(text).strip()
        ]

    def analyze_local_image(self, image_bytes, task, strict=True):
        readings = self.read_text(image_bytes)
        candidates = []
        for reading in readings:
            text, confidence = reading['text'], reading['confidence']
            # Match complete digit runs, never a phone-length substring of a longer ID.
            # Keep letters in the transcription so ambiguous digits aren't repaired.
            for match in re.finditer(r"\+?[0-9০-৯]+(?:[\s().-]+[0-9০-৯]+)*", text):
                if (match.start() and text[match.start() - 1].isalnum()
                        or match.end() < len(text) and text[match.end()].isalnum()):
                    continue
                candidates.append({'text': match.group(), 'confidence': float(confidence)})
        return {'numbers': candidates}

    @staticmethod
    def prepare_image(image_bytes):
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.width * image.height > 20_000_000:
                    raise InvalidOCRImage("Image exceeds the 20 megapixel limit.")
                image.load()
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((2400, 2400))
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                return buffer.getvalue()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
            raise InvalidOCRImage("Upload a valid image of at most 20 megapixels.") from exc

    def extract_text(self, image_bytes):
        return self.read_text(self.prepare_image(image_bytes))

    operator_map = {
        "013": "Grameenphone (GP)", "017": "Grameenphone (GP)",
        "014": "Banglalink", "019": "Banglalink", "015": "Teletalk",
        "016": "Airtel", "018": "Robi",
    }
    digit_translation = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

    @classmethod
    def normalize_number(cls, value):
        if not isinstance(value, str):
            return None
        value = value.translate(cls.digit_translation).strip()
        # Remove common phone formatting; never repair or invent digits.
        value = re.sub(r"[\s().-]", "", value)
        if value.startswith("00880"):
            value = value[4:]
        elif value.startswith("+880"):
            value = value[3:]
        elif value.startswith("880"):
            value = value[2:]
        return value if re.fullmatch(r"01[3-9][0-9]{8}", value) else None

    def parse_result(self, payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("numbers"), list):
            raise OCREngineError("The OCR provider returned an invalid response. Please scan again.")
        unique = {}
        for candidate in payload["numbers"]:
            if not isinstance(candidate, dict):
                raise OCREngineError("The OCR provider returned an invalid number entry.")
            number = self.normalize_number(candidate.get("text"))
            if number is None:
                continue
            confidence = candidate.get("confidence")
            if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
                    or not math.isfinite(confidence) or not 0 <= confidence <= 1):
                raise OCREngineError("The OCR provider returned an invalid confidence score.")
            if number not in unique or confidence > unique[number]["confidence"]:
                unique[number] = {
                    "number": number, "carrier": self.operator_map[number[:3]],
                    "carrier_code": number[:3], "confidence": confidence,
                }
        numbers = list(unique.values())
        first = numbers[0] if numbers else {}
        speech = (f"মোবাইল নম্বর শনাক্ত হয়েছে: {', '.join(unique)}।"
                  if numbers else "ছবিতে কোনো বৈধ বাংলাদেশি মোবাইল নম্বর পাওয়া যায়নি। আরও পরিষ্কার ছবি দিন।")
        return {
            "found": bool(numbers), "numbers": numbers,
            "extracted_number": first.get("number", ""),
            "carrier": first.get("carrier", ""),
            "confidence": first.get("confidence", 0.0),
            "carrier_note": "Prefix-based original carrier; ported numbers may use another network.",
            "bangla_speech": speech,
        }

    def extract_mobile_number(self, image_bytes, analyzer=None):
        prepared = self.prepare_image(image_bytes)
        if analyzer is None:
            analyzer = self.analyze_local_image
        try:
            payload = analyzer(prepared, "number_ocr", strict=True)
        except OCREngineError:
            raise
        except Exception as exc:
            raise OCREngineError("Number OCR is unavailable. Check the local OCR installation and try again.") from exc
        return self.parse_result(payload)


ocr_service = OCRService()

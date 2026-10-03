import io
import unittest
import sys
import types
from unittest.mock import patch, AsyncMock, MagicMock

from PIL import Image
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.services.ocr_service import OCRService, InvalidOCRImage, OCREngineError
from backend.routes.extract_number import router, get_database


def image_bytes():
    buffer = io.BytesIO()
    Image.new('RGB', (320, 100), 'white').save(buffer, 'PNG')
    return buffer.getvalue()


class OCRTests(unittest.TestCase):
    def setUp(self):
        self.service = OCRService()

    def test_local_international_and_bangla_digits(self):
        for value in ['01712345678', '+880 1712-345678', '8801712345678',
                      '008801712345678', '০১৭১২৩৪৫৬৭৮', '+৮৮০ ১৭১২-৩৪৫৬৭৮']:
            with self.subTest(value=value):
                self.assertEqual(self.service.normalize_number(value), '01712345678')

    def test_invalid_numbers_are_not_repaired(self):
        for value in ['01212345678', '0171234567', '017123456789',
                      '901712345678', '017I2345678', 'phone 01712345678', None, 1712345678]:
            self.assertIsNone(self.service.normalize_number(value))

    def test_carriers_and_deduplication(self):
        candidates = [{'text': prefix + '12345678', 'confidence': 0.8}
                      for prefix in self.service.operator_map]
        candidates.append({'text': '+8801312345678', 'confidence': 0.9})
        result = self.service.parse_result({'numbers': candidates})
        self.assertEqual(len(result['numbers']), 7)
        self.assertEqual(result['numbers'][0]['confidence'], 0.9)
        for item in result['numbers']:
            self.assertEqual(item['carrier'], self.service.operator_map[item['carrier_code']])

    def test_no_numbers(self):
        result = self.service.parse_result({'numbers': [{'text': '12345', 'confidence': 0.8}]})
        self.assertFalse(result['found'])
        self.assertEqual(result['extracted_number'], '')
        self.assertEqual(result['confidence'], 0)

    def test_malformed_provider_output(self):
        for value in [{}, {'numbers': None}, {'numbers': ['01712345678']},
                      {'numbers': [{'text': '01712345678', 'confidence': float('nan')}]},
                      {'numbers': [{'text': '01712345678', 'confidence': 95}]}]:
            with self.assertRaises(OCREngineError):
                self.service.parse_result(value)

    def test_image_is_processed_and_sent_to_provider(self):
        seen = []
        def analyze(data, task, strict):
            seen.append((Image.open(io.BytesIO(data)).size, task, strict))
            return {'numbers': [{'text': '01712345678', 'confidence': 0.8}]}
        result = self.service.extract_mobile_number(image_bytes(), analyzer=analyze)
        self.assertTrue(result['found'])
        self.assertEqual(seen, [((320, 100), 'number_ocr', True)])

    def test_bad_image_and_provider_error(self):
        with self.assertRaises(InvalidOCRImage):
            self.service.extract_mobile_number(b'not an image')
        def fail(*args, **kwargs):
            raise RuntimeError('network timeout')
        with self.assertRaises(OCREngineError):
            self.service.extract_mobile_number(image_bytes(), analyzer=fail)

    def test_default_ocr_is_local_and_reader_is_cached(self):
        reader = MagicMock()
        reader.readtext.return_value = [
            ([], 'Mobile: +880 1712-345678', 0.9),
            ([], '০১৮১২৩৪৫৬৭৮', 0.8),
            ([], '017123456789', 0.9),
            ([], '017I2345678', 0.9),
            ([], '01912345678, 01712345678', 0.7),
        ]
        factory = MagicMock(return_value=reader)
        with patch.dict(sys.modules, {'easyocr': types.SimpleNamespace(Reader=factory)}):
            for _ in range(2):
                result = self.service.extract_mobile_number(image_bytes())
        factory.assert_called_once_with(['bn', 'en'], gpu=False, verbose=False)
        self.assertEqual([item['number'] for item in result['numbers']],
                         ['01712345678', '01812345678', '01912345678'])
        self.assertEqual(result['numbers'][0]['confidence'], 0.9)

    def test_missing_local_engine_has_actionable_error(self):
        with patch.dict(sys.modules, {'easyocr': None}):
            with self.assertRaisesRegex(OCREngineError, 'requirements-ocr.txt'):
                self.service.extract_mobile_number(image_bytes())


class RouteTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.database = type('Database', (), {'scan_history': AsyncMock()})()
        app.dependency_overrides[get_database] = lambda: self.database
        self.client = TestClient(app)

    def upload(self, data=None, mime='image/png'):
        return self.client.post('/api/v1/ocr/extract-number',
                                files={'file': ('scan.png', image_bytes() if data is None else data, mime)})

    def test_found_and_not_found_responses(self):
        for candidates in [[], [{'text': '+8801712345678', 'confidence': 0.85}]]:
            result = OCRService().parse_result({'numbers': candidates})
            with patch('backend.routes.extract_number.ocr_service.extract_mobile_number', return_value=result):
                response = self.upload()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['found'], bool(candidates))
            self.assertTrue(response.json()['success'])
        self.assertEqual(self.database.scan_history.insert_one.await_count, 2)

    def test_upload_limits_and_invalid_image(self):
        self.assertEqual(self.upload(b'bad', 'text/plain').status_code, 400)
        self.assertEqual(self.upload(b'bad').status_code, 400)
        self.assertEqual(self.upload(b'').status_code, 400)
        with patch('backend.routes.extract_number.MAX_UPLOAD_BYTES', 10):
            self.assertEqual(self.upload(b'x' * 11).status_code, 413)

    def test_provider_errors_are_not_success(self):
        with patch('backend.routes.extract_number.ocr_service.extract_mobile_number',
                   side_effect=OCREngineError('OCR unavailable')):
            self.assertEqual(self.upload().status_code, 502)
        self.database.scan_history.insert_one.assert_not_awaited()

    def test_database_failure_preserves_scan(self):
        self.database.scan_history.insert_one.side_effect = RuntimeError('offline')
        result = OCRService().parse_result({'numbers': []})
        with patch('backend.routes.extract_number.ocr_service.extract_mobile_number', return_value=result):
            self.assertEqual(self.upload().status_code, 200)


class GeminiOCRTests(unittest.TestCase):
    def test_ocr_model_prompt_and_timeout(self):
        from backend.services.gemini_service import GeminiService
        model = MagicMock()
        model.generate_content.return_value.text = '{"numbers": []}'
        with patch('backend.services.gemini_service.API_KEY', 'test-key'), \
             patch('backend.services.gemini_service.genai.GenerativeModel', return_value=model), \
             patch.dict('os.environ', {'OCR_GEMINI_MODEL': 'test-ocr-model'}):
            service = GeminiService()
            self.assertEqual(service.analyze_image(image_bytes(), 'number_ocr', strict=True), {'numbers': []})
        args, kwargs = model.generate_content.call_args
        self.assertIsInstance(args[0][0], Image.Image)
        self.assertIn('Do not guess', args[0][1])
        self.assertEqual(kwargs['request_options']['timeout'], 30)

    def test_provider_and_json_errors_are_raised(self):
        from backend.services.gemini_service import GeminiService
        model = MagicMock()
        with patch('backend.services.gemini_service.API_KEY', 'test-key'), \
             patch('backend.services.gemini_service.genai.GenerativeModel', return_value=model):
            service = GeminiService()
            model.generate_content.side_effect = RuntimeError('timeout')
            with self.assertRaises(RuntimeError):
                service.analyze_image(image_bytes(), 'number_ocr', strict=True)
            model.generate_content.side_effect = None
            model.generate_content.return_value.text = 'not json'
            with self.assertRaises(RuntimeError):
                service.analyze_image(image_bytes(), 'number_ocr', strict=True)


if __name__ == '__main__':
    unittest.main()

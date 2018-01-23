from django.test import SimpleTestCase
from .ocr_clean import OCRLine

class TestOCRLine(SimpleTestCase):
    def test_duplicate_line(self):
        ocrline1 = OCRLine(199,735,201,1252,173,1252,171,735)
        ocrline2 = OCRLine(209,733,218,1252,175,1253,166,733)
        ocrline3 = OCRLine(262,731,265,1250,221,1250,218,731)
        self.assertTrue(OCRLine.is_duplicate_line(ocrline1, ocrline2))
        self.assertFalse(OCRLine.is_duplicate_line(ocrline1, ocrline3))
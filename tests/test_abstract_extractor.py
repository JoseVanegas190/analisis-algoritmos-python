import unittest

from src.abstract_extractor import extract_abstract_from_text


class ExtractAbstractTests(unittest.TestCase):
    def test_extracts_abstract_until_keywords(self):
        text = """Title\nABSTRACT\nFirst line of the abstract.\nSecond line.\nKeywords: AI, education\n1. Introduction\n"""
        self.assertEqual(
            extract_abstract_from_text(text),
            "First line of the abstract. Second line.",
        )

    def test_accepts_spaced_heading_and_numbered_introduction(self):
        text = """A B S T R A C T\nA compact summary.\n1. Introduction\nBody\n"""
        self.assertEqual(extract_abstract_from_text(text), "A compact summary.")

    def test_accepts_marker_with_content_on_same_line(self):
        text = "Abstract: Summary on the same line.\nKeywords: extraction\n"
        self.assertEqual(extract_abstract_from_text(text), "Summary on the same line.")

    def test_handles_keywords_before_abstract_in_extracted_order(self):
        text = """A B S T R A C T\nKeywords:\nAI\nEducation\nThis is the actual abstract text and it is deliberately long enough to identify the beginning.\n1. Introduction\n"""
        self.assertEqual(
            extract_abstract_from_text(text),
            "This is the actual abstract text and it is deliberately long enough to identify the beginning.",
        )

    def test_accepts_spanish_marker(self):
        text = """RESUMEN\nTexto principal del resumen.\nPalabras clave: prueba\n"""
        self.assertEqual(extract_abstract_from_text(text), "Texto principal del resumen.")

    def test_returns_none_without_marker(self):
        self.assertIsNone(extract_abstract_from_text("Title\nIntroduction\nBody"))


if __name__ == "__main__":
    unittest.main()

import unittest
from backend.services.article_extractor import ArticleExtractor

class TestArticleExtraction(unittest.TestCase):
    
    def test_extract_from_text(self):
        text = "This is a sample news article text. It has some facts."
        result = ArticleExtractor.extract_from_text(text)
        
        self.assertEqual(result['title'], "Pasted Article")
        self.assertEqual(result['source'], "Pasted Text")
        self.assertIn("sample news article", result['text'])
        
    def test_extract_from_empty_text(self):
        with self.assertRaises(Exception):
            ArticleExtractor.extract_from_text("   ")

if __name__ == '__main__':
    unittest.main()

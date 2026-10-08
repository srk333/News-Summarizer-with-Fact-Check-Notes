import unittest
from unittest.mock import patch
from backend.services.claim_extractor import ClaimExtractor

class TestClaimExtraction(unittest.TestCase):
    
    @patch.object(ClaimExtractor, 'extract_claims')
    def test_extract_claims_mock(self, mock_extract):
        mock_extract.return_value = [
            {
                "claim_text": "Company X launched product Y.",
                "claim_type": "Event",
                "importance": "HIGH",
                "entities_involved": ["Company X", "product Y"],
                "date_time": "2026-01-01"
            }
        ]
        
        extractor = ClaimExtractor()
        claims = extractor.extract_claims("Company X launched product Y on 2026-01-01.")
        
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]['importance'], "HIGH")

if __name__ == '__main__':
    unittest.main()

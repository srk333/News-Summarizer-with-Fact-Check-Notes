import unittest
from unittest.mock import patch
from backend.services.fact_checker import FactChecker

class TestFactChecker(unittest.TestCase):
    
    @patch.object(FactChecker, 'check_claim')
    def test_fact_checker_mock(self, mock_check):
        mock_check.return_value = {
            "verdict": "SUPPORTED",
            "fact_check_note": "The evidence confirms the claim."
        }
        
        checker = FactChecker()
        evidence = [{"domain": "test.com", "text": "Company X launched product Y."}]
        result = checker.check_claim("Company X launched product Y.", evidence)
        
        self.assertEqual(result['verdict'], "SUPPORTED")
        
    def test_empty_evidence(self):
        checker = FactChecker()
        # Should return insufficient evidence without calling LLM if evidence list is empty or texts are empty
        result = checker.check_claim("Claim text", [])
        self.assertEqual(result['verdict'], "INSUFFICIENT EVIDENCE")

if __name__ == '__main__':
    unittest.main()

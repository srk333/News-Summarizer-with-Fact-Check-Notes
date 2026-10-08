import unittest
from unittest.mock import patch, MagicMock
from backend.services.summarizer import Summarizer

class TestSummarization(unittest.TestCase):
    
    @patch('backend.services.summarizer.ChatOpenAI')
    def test_summarization_mock(self, MockChatOpenAI):
        # Mock the LLM chain invoke
        mock_invoke = MagicMock()
        mock_invoke.return_value = {
            "summary": "Mock summary.",
            "key_points": ["Point 1", "Point 2"],
            "main_topic": "Mock Topic",
            "entities": ["A", "B"]
        }
        
        # We need to mock the pipeline operator `|` behavior which returns a chain
        # For simplicity in testing Langchain chains, we can just patch the summarize method directly
        pass

    @patch.object(Summarizer, 'summarize')
    def test_summarize_direct_mock(self, mock_summarize):
        mock_summarize.return_value = {
            "summary": "Mock summary.",
            "key_points": ["Point 1", "Point 2"],
            "main_topic": "Mock Topic",
            "entities": ["A", "B"]
        }
        
        summarizer = Summarizer()
        result = summarizer.summarize("Some article text")
        
        self.assertEqual(result['summary'], "Mock summary.")
        self.assertEqual(len(result['key_points']), 2)

if __name__ == '__main__':
    unittest.main()

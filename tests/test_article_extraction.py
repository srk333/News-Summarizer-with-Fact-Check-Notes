import json
import unittest
from unittest.mock import MagicMock, patch

from backend.services.article_extractor import (
    ArticleExtractor,
    _extract_msn_article_id,
    _extract_msn_locale,
    _unwrap_aggregator_url,
)


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

    def test_msn_id_and_locale_from_url(self):
        url = "https://www.msn.com/en-in/news/other/ar-rahman-launches-tamil-idol/ar-AA2aisMU"
        self.assertEqual(_extract_msn_article_id(url), "AA2aisMU")
        self.assertEqual(_extract_msn_locale(url), "en-in")
        query_url = url + "?ocid=BingNews"
        self.assertEqual(_extract_msn_article_id(query_url), "AA2aisMU")

    def test_msn_slideshow_id_from_url(self):
        url = (
            "https://www.msn.com/en-in/news/other/"
            "5-clear-signs-your-crush-is-falling-in-love-with-you/ss-AA1Yysmq"
            "?uxmode=ruby&ctsrc=dgst&ocid="
        )
        self.assertEqual(_extract_msn_article_id(url), "AA1Yysmq")

    def test_unwrap_bing_article_url(self):
        wrapped = "https://www.bing.com/news/apiclick?articleurl=https%3A%2F%2Fwww.bbc.com%2Fnews%2Fworld-123"
        self.assertEqual(_unwrap_aggregator_url(wrapped), "https://www.bbc.com/news/world-123")

    @patch('backend.services.article_extractor._http_get')
    def test_extract_msn_via_detail_api(self, mock_get):
        body = "<p>" + ("AR Rahman launched Tamil Idol with Sony Vizha. " * 8) + "</p>"
        payload = {
            "title": "AR Rahman launches Tamil Idol",
            "body": body,
            "provider": {"name": "Cinema Express"},
            "sourceHref": "https://www.cinemaexpress.com/tamil/news/example",
        }
        response = MagicMock()
        response.json.return_value = payload
        mock_get.return_value = response

        url = "https://www.msn.com/en-in/news/other/ar-rahman-launches-tamil-idol/ar-AA2aisMU"
        result = ArticleExtractor.extract_from_url(url)

        self.assertEqual(result['title'], "AR Rahman launches Tamil Idol")
        self.assertEqual(result['source'], "Cinema Express")
        self.assertIn("Tamil Idol", result['text'])
        self.assertGreaterEqual(len(result['text']), 100)
        mock_get.assert_called()
        called_url = mock_get.call_args[0][0]
        self.assertIn("/Detail/en-in/AA2aisMU", called_url)

    @patch('backend.services.article_extractor._http_get')
    def test_extract_msn_slideshow_from_slides(self, mock_get):
        payload = {
            "title": "5 clear signs your crush is falling in love with you",
            "body": "",
            "type": "slideshow",
            "provider": {"name": "Times of India"},
            "slides": [
                {
                    "title": "They make time for you",
                    "body": "<p>" + ("They rearrange their schedule just to see you. " * 6) + "</p>",
                },
                {
                    "title": "They remember small details",
                    "body": "<p>" + ("They recall things you mentioned weeks ago. " * 6) + "</p>",
                },
            ],
        }
        response = MagicMock()
        response.json.return_value = payload
        mock_get.return_value = response

        url = (
            "https://www.msn.com/en-in/news/other/"
            "5-clear-signs-your-crush-is-falling-in-love-with-you/ss-AA1Yysmq"
        )
        result = ArticleExtractor.extract_from_url(url)

        self.assertEqual(result['title'], "5 clear signs your crush is falling in love with you")
        self.assertEqual(result['source'], "Times of India")
        self.assertIn("rearrange their schedule", result['text'])
        self.assertIn("remember small details", result['text'].lower())
        called_url = mock_get.call_args[0][0]
        self.assertIn("/Detail/en-in/AA1Yysmq", called_url)

    @patch('backend.services.article_extractor._http_get')
    def test_extract_from_json_ld_html(self, mock_get):
        article_body = "Scientists announced a major climate finding. " * 10
        html = f"""
        <html>
          <head>
            <title>Ignore me</title>
            <meta property="og:title" content="Climate Finding">
            <script type="application/ld+json">
            {json.dumps({
                "@type": "NewsArticle",
                "headline": "Climate Finding",
                "articleBody": article_body,
            })}
            </script>
          </head>
          <body><p>too short</p></body>
        </html>
        """
        response = MagicMock()
        response.text = html
        response.url = "https://www.example.com/climate"
        mock_get.return_value = response

        with patch('backend.services.article_extractor._is_msn_url', return_value=False), \
             patch('backend.services.article_extractor._extract_via_newspaper', return_value=None):
            result = ArticleExtractor.extract_from_url("https://www.example.com/climate")

        self.assertEqual(result['title'], "Climate Finding")
        self.assertIn("climate finding", result['text'].lower())


if __name__ == '__main__':
    unittest.main()

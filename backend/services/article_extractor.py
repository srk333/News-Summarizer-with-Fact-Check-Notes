import requests
from bs4 import BeautifulSoup
from backend.utils.helpers import clean_text

class ArticleExtractor:
    @staticmethod
    def extract_from_url(url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, etc.
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
                
            title = soup.title.string if soup.title else ""
            
            # Simple heuristic: find paragraphs
            paragraphs = soup.find_all('p')
            text = " ".join([p.get_text() for p in paragraphs])
            text = clean_text(text)
            
            return {
                'title': title.strip(),
                'text': text,
                'source': url
            }
        except Exception as e:
            raise Exception(f"Failed to extract article from URL: {str(e)}")
            
    @staticmethod
    def extract_from_text(text):
        if not text.strip():
            raise Exception("Empty text provided")
        return {
            'title': "Pasted Article",
            'text': clean_text(text),
            'source': "Pasted Text"
        }

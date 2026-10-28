import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from backend.utils.helpers import clean_text
import re

# Browser-like headers that defeat most bot checks
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}


class ArticleExtractor:

    @staticmethod
    def extract_from_url(url):
        """Try multiple strategies to extract article text from a URL."""
        last_error = None

        # Strategy 1: newspaper3k (best for news sites)
        try:
            from newspaper import Article as NewspaperArticle
            article = NewspaperArticle(url, browser_user_agent=HEADERS['User-Agent'])
            article.download()
            article.parse()
            text = clean_text(article.text)
            if text and len(text) >= 100:
                title = article.title or _extract_title_from_url(url)
                source = _get_domain(url)
                return {'title': title.strip(), 'text': text, 'source': source}
        except Exception as e:
            last_error = e

        # Strategy 2: requests + smart BeautifulSoup parsing
        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            response = session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            text, title = _parse_html(response.text)
            if text and len(text) >= 100:
                return {'title': title, 'text': text, 'source': _get_domain(url)}
        except Exception as e:
            last_error = e

        # All strategies failed
        raise Exception(
            f"Could not extract article content from this URL. "
            f"This often happens with MSN, Bing, and paywalled sites that block scrapers. "
            f"Please copy and paste the article text directly instead."
        )

    @staticmethod
    def extract_from_text(text):
        if not text or not text.strip():
            raise Exception("Empty text provided")
        return {
            'title': 'Pasted Article',
            'text': clean_text(text),
            'source': 'Pasted Text'
        }


def _parse_html(html):
    """Smart HTML parser — tries semantic tags first, falls back to <p> tags."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove junk
    for tag in soup(["script", "style", "nav", "footer", "header",
                      "aside", "form", "iframe", "noscript", "button"]):
        tag.decompose()

    title = ""
    if soup.title:
        title = soup.title.get_text().strip()

    # Try meta og:title for a cleaner title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()

    # Try structured article containers first
    article_text = ""
    for selector in ['article', '[role="main"]', 'main', '.article-body',
                     '.story-body', '.content-body', '.post-content',
                     '.entry-content', '#article-body', '.article__body']:
        container = soup.select_one(selector)
        if container:
            paragraphs = container.find_all('p')
            article_text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            article_text = clean_text(article_text)
            if len(article_text) >= 100:
                return article_text, title

    # Final fallback: all <p> tags on the page
    paragraphs = soup.find_all('p')
    article_text = " ".join(p.get_text(" ", strip=True) for p in paragraphs
                            if len(p.get_text(strip=True)) > 40)
    article_text = clean_text(article_text)
    return article_text, title


def _get_domain(url):
    try:
        return urlparse(url).netloc.replace('www.', '')
    except Exception:
        return 'Unknown'


def _extract_title_from_url(url):
    try:
        path = urlparse(url).path
        slug = path.rstrip('/').split('/')[-1]
        return slug.replace('-', ' ').replace('_', ' ').title()
    except Exception:
        return 'Article'

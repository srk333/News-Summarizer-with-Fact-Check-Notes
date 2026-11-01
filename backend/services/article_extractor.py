import json
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from backend.utils.helpers import clean_text

MIN_TEXT_LEN = 100          # minimum for pasted text
MIN_ARTICLE_LEN = 400       # minimum for text extracted from a URL
MAX_FOLLOW_DEPTH = 2

IMAGE_EXT = re.compile(r'\.(?:jpe?g|png|gif|webp|svg|avif)(?:\?|$)', re.IGNORECASE)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

JSON_HEADERS = {
    **HEADERS,
    'Accept': 'application/json, text/plain, */*',
}

MSN_DETAIL_API = 'https://assets.msn.com/content/view/v2/Detail/{locale}/{article_id}'


class ArticleExtractor:

    @staticmethod
    def extract_from_url(url, _depth=0):
        """Try multiple strategies; accept only results that look like a real article."""
        if not url or not str(url).strip():
            raise Exception("Empty URL provided")

        url = _unwrap_aggregator_url(url.strip())
        last_error = None

        strategies = []
        if _is_msn_url(url):
            strategies.append(('msn', lambda: _extract_from_msn(url, _depth=_depth)))
        strategies += [
            ('newspaper', lambda: _extract_via_newspaper(url)),
            ('html', lambda: _extract_from_html(url)),
            ('jina', lambda: _extract_via_jina(url)),
        ]

        for name, run in strategies:
            try:
                result = _sanitize(run())
                if _is_article(result):
                    if not result['title']:
                        result['title'] = _extract_title_from_url(url)
                    print(f"[extractor] used '{name}': {len(result['text'])} chars")
                    return result
                size = len((result or {}).get('text') or '')
                print(f"[extractor] '{name}' rejected ({size} chars, not article-like)")
            except Exception as e:
                last_error = e
                print(f"[extractor] '{name}' failed: {e}")

        detail = f" ({last_error})" if last_error else ""
        raise Exception(
            "Could not extract the article text from this URL. "
            "The page may be paywalled, block automated access, or load only in a browser. "
            "Please copy the article text and use the Paste Text tab instead."
            + detail
        )

    @staticmethod
    def extract_from_text(text):
        if not text or not text.strip():
            raise Exception("Empty text provided")
        return {
            'title': 'Pasted Article',
            'text': clean_text(text),
            'source': 'Pasted Text',
        }


def _is_usable(text):
    return bool(text) and len(text) >= MIN_TEXT_LEN


def _sanitize(result):
    """Strip junk (image links, 'Final URL:' lines) and reject bad titles."""
    if not result:
        return None
    text = result.get('text') or ''
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)                       # markdown images
    text = re.sub(r'(?i)\b(?:Final URL|URL Source)\s*:\s*\S+', ' ', text)   # reader-tool labels
    text = re.sub(r'(?i)https?://\S+\.(?:jpe?g|png|gif|webp|svg|avif)\S*', ' ', text)
    text = clean_text(text)

    title = (result.get('title') or '').strip()
    if re.match(r'(?i)https?://', title) or IMAGE_EXT.search(title):
        title = ''
    return {**result, 'title': title, 'text': text}


def _is_article(result):
    """Real article text is long, has many words and several sentences."""
    text = (result or {}).get('text') or ''
    if len(text) < MIN_ARTICLE_LEN:
        return False
    if len(text.split()) < 60:
        return False
    return len(re.findall(r'[.!?\u0964](?:\s|$)', text)) >= 3


def _http_get(url, headers=None, timeout=20):
    session = requests.Session()
    session.headers.update(headers or HEADERS)
    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response


def _is_msn_url(url):
    host = urlparse(url).netloc.lower()
    return host.endswith('msn.com') or host.endswith('msn.cn')


def _extract_msn_article_id(url):
    path = urlparse(url).path
    # Articles (ar-), slideshows (ss-), videos (vi-), and gem clusters (gm-)
    match = re.search(r'/(?:ar|ss|vi|gm)-([A-Za-z0-9]+)/?$', path, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(
        r'/(?:ar|ss|vi|gm)-([A-Za-z]{2}[A-Za-z0-9]{4,})(?:/|$|\?)',
        path,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _extract_msn_locale(url):
    match = re.search(r'msn\.(?:com|cn)/([a-z]{2}-[a-z]{2,4})/', url, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return 'en-us'


def _extract_from_msn(url, _depth=0):
    article_id = _extract_msn_article_id(url)
    if not article_id:
        return None

    locale = _extract_msn_locale(url)
    data = None
    last_error = None
    for candidate in _unique([locale, 'en-us', 'en-in', 'en-gb']):
        try:
            api_url = MSN_DETAIL_API.format(locale=candidate, article_id=article_id)
            response = _http_get(api_url, headers=JSON_HEADERS, timeout=20)
            payload = response.json()
            if isinstance(payload, dict) and (
                payload.get('body')
                or payload.get('slides')
                or payload.get('title')
                or payload.get('abstract')
            ):
                data = payload
                break
        except Exception as e:
            last_error = e

    if not data:
        if last_error:
            raise last_error
        return None

    title = (data.get('title') or '').strip() or _extract_title_from_url(url)
    text = _msn_text_from_payload(data)

    provider = ''
    provider_obj = data.get('provider')
    if isinstance(provider_obj, dict):
        provider = provider_obj.get('name') or ''
    source = provider.strip() or _get_domain(url)

    source_href = data.get('sourceHref') or ''
    if _depth < MAX_FOLLOW_DEPTH and source_href.startswith('http') and not _is_usable(text):
        try:
            original = ArticleExtractor.extract_from_url(source_href, _depth=_depth + 1)
            if original and _is_usable(original.get('text')):
                original['title'] = original.get('title') or title
                original['source'] = original.get('source') or source
                return original
        except Exception:
            pass

    if not _is_usable(text):
        return None

    return {'title': title, 'text': text, 'source': source}


def _msn_text_from_payload(data):
    parts = []
    body = _html_to_text(data.get('body') or '')
    if body:
        parts.append(body)

    for slide in data.get('slides') or []:
        if not isinstance(slide, dict):
            continue
        slide_title = clean_text(slide.get('title') or '')
        slide_body = _html_to_text(slide.get('body') or '')
        if slide_title and slide_title not in parts:
            parts.append(slide_title)
        if slide_body:
            parts.append(slide_body)

    if not any(_is_usable(part) for part in parts):
        abstract = clean_text(data.get('abstract') or '')
        if abstract:
            parts.append(abstract)

    return clean_text(' '.join(parts))


def _extract_via_newspaper(url):
    from newspaper import Article as NewspaperArticle
    article = NewspaperArticle(url, browser_user_agent=HEADERS['User-Agent'])
    article.download()
    article.parse()
    text = clean_text(article.text)
    if not _is_usable(text):
        return None
    title = article.title or _extract_title_from_url(url)
    return {
        'title': title.strip(),
        'text': text,
        'source': _get_domain(url),
    }


def _extract_from_html(url):
    response = _http_get(url, timeout=20)
    html = response.text
    text, title = _parse_html(html)
    title = title or _extract_title_from_url(url)
    result = {
        'title': title,
        'text': text,
        'source': _get_domain(str(response.url) or url),
    }
    if _is_usable(text):
        return result

    canonical = _find_canonical_url(html)
    if canonical and canonical.rstrip('/') != url.rstrip('/') and not _is_msn_url(url):
        try:
            followed = ArticleExtractor.extract_from_url(canonical, _depth=MAX_FOLLOW_DEPTH)
            if followed and _is_usable(followed.get('text')):
                return followed
        except Exception:
            pass
    return result if _is_usable(result.get('text')) else None


def _extract_via_jina(url):
    """Fallback for JavaScript-rendered pages using Jina's public reader."""
    reader_url = 'https://r.jina.ai/' + url
    response = _http_get(
        reader_url,
        headers={**HEADERS, 'Accept': 'text/plain'},
        timeout=30,
    )
    raw = response.text or ''
    lowered = raw.lower()
    if not raw or 'failed to' in lowered[:240]:
        return None
    if any(marker in lowered for marker in (
        'not yet fully loaded',
        'shadow dom that are currently hidden',
        'enable javascript',
        'just a moment',
    )):
        return None

    title = _extract_title_from_url(url)
    title_match = re.search(r'(?im)^Title:\s*(.+)$', raw)
    if title_match:
        title = title_match.group(1).strip() or title

    body = re.sub(r'(?im)^Title:\s*.+$', '', raw, count=1)
    body = re.sub(r'(?im)^URL Source:\s*.+$', '', body)
    body = re.sub(r'(?im)^Markdown Content:\s*', '', body)
    body = re.sub(r'(?im)^Published Time:\s*.+$', '', body)
    text = clean_text(body)
    if not _is_usable(text):
        return None
    return {'title': title, 'text': text, 'source': _get_domain(url)}


def _parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    title = _extract_title(soup)
    json_ld_text, json_ld_title = _extract_json_ld(soup)
    if json_ld_title:
        title = json_ld_title
    if _is_usable(json_ld_text):
        return json_ld_text, title

    for tag in soup(["script", "style", "nav", "footer", "header",
                      "aside", "form", "iframe", "noscript", "button"]):
        tag.decompose()

    for selector in [
        'article', '[role="main"]', 'main', '.article-body',
        '.story-body', '.content-body', '.post-content',
        '.entry-content', '#article-body', '.article__body',
        '.RichText-body', '.article-content', '[itemprop="articleBody"]',
    ]:
        container = soup.select_one(selector)
        if container:
            article_text = clean_text(container.get_text(" ", strip=True))
            if _is_usable(article_text):
                return article_text, title

    paragraphs = soup.find_all('p')
    article_text = " ".join(
        p.get_text(" ", strip=True)
        for p in paragraphs
        if len(p.get_text(strip=True)) > 40
    )
    return clean_text(article_text), title


def _extract_title(soup):
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    if soup.title:
        return soup.title.get_text().strip()
    return ''


def _extract_json_ld(soup):
    for script in soup.find_all('script', type='application/ld+json'):
        raw = script.string or script.get_text() or ''
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        article = _find_news_article(data)
        if not article:
            continue
        body = article.get('articleBody') or article.get('description') or ''
        if isinstance(body, list):
            body = ' '.join(str(part) for part in body)
        title = article.get('headline') or article.get('name') or ''
        text = clean_text(str(body))
        if _is_usable(text) or title:
            return text, str(title).strip()
    return '', ''


def _find_news_article(data):
    if isinstance(data, list):
        for item in data:
            found = _find_news_article(item)
            if found:
                return found
        return None
    if not isinstance(data, dict):
        return None
    types = data.get('@type')
    type_list = types if isinstance(types, list) else [types]
    type_list = [str(t).lower() for t in type_list if t]
    if any(t in ('newsarticle', 'article', 'reportagearticle', 'blogposting') for t in type_list):
        return data
    graph = data.get('@graph')
    if graph:
        return _find_news_article(graph)
    return None


def _find_canonical_url(html):
    soup = BeautifulSoup(html, 'html.parser')
    link = soup.find('link', rel=lambda value: value and 'canonical' in value)
    if link and link.get('href', '').startswith('http'):
        return link['href'].strip()
    og_url = soup.find('meta', property='og:url')
    if og_url and og_url.get('content', '').startswith('http'):
        return og_url['content'].strip()
    return ''


def _html_to_text(html):
    if not html:
        return ''
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    return clean_text(soup.get_text(' ', strip=True))


def _unwrap_aggregator_url(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    query = parse_qs(parsed.query)

    for key in ('articleurl', 'url', 'u', 'r'):
        values = query.get(key) or []
        if not values:
            continue
        candidate = unquote(values[0]).strip()
        if candidate.startswith('http://') or candidate.startswith('https://'):
            return candidate

    if 'news.google.com' in host or 'bing.com' in host:
        for values in query.values():
            for value in values:
                candidate = unquote(value).strip()
                if candidate.startswith('http') and 'msn.com' in candidate:
                    return candidate
    return url


def _get_domain(url):
    try:
        return urlparse(url).netloc.replace('www.', '')
    except Exception:
        return 'Unknown'


def _extract_title_from_url(url):
    try:
        path = urlparse(url).path
        slug = path.rstrip('/').split('/')[-1]
        slug = re.sub(r'^ar-[A-Za-z0-9]+$', '', slug) or slug
        cleaned = slug.replace('-', ' ').replace('_', ' ').strip()
        return cleaned.title() if cleaned else 'Article'
    except Exception:
        return 'Article'


def _unique(items):
    seen = set()
    ordered = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
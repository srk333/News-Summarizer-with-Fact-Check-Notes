import re
from urllib.parse import urlparse

def get_domain(url):
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "")
    except:
        return "Unknown"

def determine_source_quality(domain):
    high_trust = ['.gov', '.edu', 'reuters.com', 'apnews.com', 'bbc.com', 'npr.org']
    medium_trust = ['.org', 'nytimes.com', 'wsj.com', 'cnn.com', 'theguardian.com']
    
    domain_lower = domain.lower()
    for ht in high_trust:
        if domain_lower.endswith(ht):
            return "HIGH TRUST"
            
    for mt in medium_trust:
        if domain_lower.endswith(mt):
            return "MEDIUM TRUST"
            
    return "LOWER TRUST"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

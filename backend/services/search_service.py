import os
from tavily import TavilyClient
from backend.config import Config
from backend.utils.helpers import get_domain, determine_source_quality

class SearchService:
    def __init__(self):
        # We handle empty API keys defensively. If missing, it will raise when searched.
        api_key = Config.TAVILY_API_KEY
        if api_key:
            self.client = TavilyClient(api_key=api_key)
        else:
            self.client = None
            
    def search_evidence(self, query):
        if not self.client:
            raise Exception("Tavily API key is not configured.")
            
        try:
            # We want high quality search results
            response = self.client.search(query=query, search_depth="advanced", max_results=5)
            
            evidence_results = []
            for result in response.get('results', []):
                domain = get_domain(result.get('url'))
                quality = determine_source_quality(domain)
                
                evidence_results.append({
                    'title': result.get('title', 'No Title'),
                    'url': result.get('url', ''),
                    'domain': domain,
                    'text': result.get('content', ''),
                    'quality': quality
                })
                
            return evidence_results
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

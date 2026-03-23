"""
Web Search Hook - Search the web using different providers

Supports:
- Brave Search API
- DuckDuckGo (no API key required)
- Google Custom Search (requires API key)
- SearXNG (self-hosted)
"""

import os
import json
from typing import Optional
try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx
import sys

try:
    from ..main import OLLAMA_URL
except ImportError:
    OLLAMA_URL = "http://localhost:11434"


class WebSearchHook:
    """Search the web using various providers."""
    
    def __init__(self):
        self.providers = {
            "brave": self._search_brave,
            "duckduckgo": self._search_duckduckgo,
            "google": self._search_google,
            "searxng": self._search_searxng,
        }
        self.default_provider = "duckduckgo"
        self._fix_ssl()
    
    def _fix_ssl(self):
        """Fix SSL certificate issues on macOS."""
        pass
    
    def _get_client(self):
        """Get httpx client with SSL workaround."""
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            return httpx.Client(follow_redirects=True)
        else:
            return httpx.Client(verify=_create_unverified_https_context(), follow_redirects=True)
    
    def run(self, query: str, provider: str = None, num_results: int = 5, **kwargs) -> dict:
        """
        Search the web.
        
        Args:
            query: Search query
            provider: Search provider (brave, duckduckgo, google, searxng)
            num_results: Number of results to return
        
        Returns:
            dict with search results
        """
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            return {"error": f"Unknown provider: {provider}", "available": list(self.providers.keys())}
        
        try:
            return self.providers[provider](query, num_results)
        except Exception as e:
            return {"error": str(e)}
    
    def _search_brave(self, query: str, num_results: int = 5) -> dict:
        """Search using Brave Search API."""
        api_key = os.environ.get("BRAVE_API_KEY")
        if not api_key:
            return {"error": "BRAVE_API_KEY not set. Get one at https://brave.com/search/api/"}
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": api_key,
            "Accept": "application/json"
        }
        params = {"q": query, "count": num_results}
        
        client = self._get_client()
        response = client.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        client.close()
        
        results = []
        for item in data.get("web", {}).get("results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", "")
            })
        
        return {"provider": "Brave", "query": query, "results": results}
    
    def _search_duckduckgo(self, query: str, num_results: int = 5) -> dict:
        """Search using Wikipedia API as fallback."""
        import urllib.parse
        
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": num_results,
            "namespace": 0,
            "format": "json"
        }
        
        headers = {
            "User-Agent": "OpenCodeChat/1.0 (https://github.com/anomalyco/opencode)"
        }
        
        client = self._get_client()
        response = client.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        client.close()
        
        results = []
        if len(data) >= 4:
            titles = data[1]
            urls = data[3]
            descriptions = data[2] if len(data) >= 3 else []
            
            for i, title in enumerate(titles[:num_results]):
                results.append({
                    "title": title,
                    "url": urls[i] if i < len(urls) else "",
                    "description": descriptions[i] if i < len(descriptions) else ""
                })
        
        if not results:
            return {
                "provider": "Wikipedia",
                "query": query,
                "results": [],
                "info": "Wikipedia search only. For full web search:"
                    + "\n  - Brave: export BRAVE_API_KEY=your_key"
                    + "\n  - Google: export GOOGLE_API_KEY=... & GOOGLE_CSE_ID=..."
                    + "\n  - SearXNG: export SEARXNG_URL=http://localhost:8888"
            }
        
        return {"provider": "Wikipedia", "query": query, "results": results}
    
    def _search_google(self, query: str, num_results: int = 5) -> dict:
        """Search using Google Custom Search API."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        cx = os.environ.get("GOOGLE_CSE_ID")
        
        if not api_key or not cx:
            return {"error": "GOOGLE_API_KEY and GOOGLE_CSE_ID required"}
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cx, "q": query, "num": min(num_results, 10)}
        
        client = self._get_client()
        response = client.get(url, params=params, timeout=30)
        data = response.json()
        client.close()
        
        results = []
        for item in data.get("items", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", "")
            })
        
        return {"provider": "Google", "query": query, "results": results}
    
    def _search_searxng(self, query: str, num_results: int = 5) -> dict:
        """Search using self-hosted SearXNG instance."""
        instance = os.environ.get("SEARXNG_URL", "http://localhost:8888")
        url = f"{instance}/search"
        params = {"q": query, "format": "json", "engines": "google,duckduckgo,bing"}
        
        client = self._get_client()
        response = client.get(url, params=params, timeout=30)
        data = response.json()
        client.close()
        
        results = []
        for item in data.get("results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("content", "")
            })
        
        return {"provider": "SearXNG", "query": query, "results": results}
    
    def fetch_and_summarize(self, url: str, max_length: int = 500, **kwargs) -> dict:
        """
        Fetch a webpage and summarize its content using LLM.
        
        Args:
            url: URL of the webpage to fetch
            max_length: Maximum length of the summary (words)
        
        Returns:
            dict with URL, title, and LLM summary
        """
        if not url:
            return {"error": "URL required", "usage": "fetch url='https://example.com'"}
        
        url = url.strip().strip("'\"")
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            client = self._get_client()
            response = client.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (compatible; OpenCodeChat/1.0)"
            })
            client.close()
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}", "url": url}
            
            html_content = response.text
            
            from html import unescape
            import re
            
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            text = unescape(text)
            text = text.strip()
            
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else url
            
            text = text[:10000]
            
            summary_prompt = f"""Summarize the following webpage content in approximately {max_length} words.
Include the main topics and key information.

Title: {title}

Content:
{text}

Summary:"""
            
            try:
                model = kwargs.get("model", "llama3.1")
                response = httpx.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": model, "prompt": summary_prompt, "stream": False},
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("response", "").strip()
                else:
                    summary = "LLM generation failed"
            except Exception as e:
                summary = f"LLM error: {str(e)}"
            
            return {
                "url": url,
                "title": title,
                "summary": summary,
                "content_length": len(text)
            }
            
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def search_with_llm_summary(self, query: str, provider: str = None) -> dict:
        """
        Search the web and use LLM to summarize results.
        
        This combines web search with local LLM for better understanding.
        """
        search_results = self.run(query, provider)
        
        if "error" in search_results:
            return search_results
        
        results_text = json.dumps(search_results["results"], indent=2)
        
        summary_prompt = f"""Based on the following web search results for "{query}", 
provide a concise summary of the key findings:

{results_text}

Summary:"""
        
        try:
            response = httpx.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": "llama3.1", "prompt": summary_prompt, "stream": False},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                search_results["summary"] = data.get("response", "")
        except:
            search_results["summary"] = "LLM summary unavailable"
        
        return search_results
    
    def help(self) -> str:
        return """
Web Search Hook
===============
Usage: /hook web_search query="your search" provider="duckduckgo" num_results=5

Providers:
- duckduckgo (default, no API key)
- brave (requires BRAVE_API_KEY)
- google (requires GOOGLE_API_KEY + GOOGLE_CSE_ID)
- searxng (requires SEARXNG_URL)

Special commands:
- /web "query" - Quick search
- /summary "query" - Search with LLM summary
"""


def quick_search(query: str) -> dict:
    """Helper function for quick searches."""
    hook = WebSearchHook()
    return hook.run(query)


if __name__ == "__main__":
    result = quick_search("Python 3.12 new features")
    print(json.dumps(result, indent=2))

"""Web Tools — WebFetch, WebSearch, Image Search, Places Search.

From: Claude Code, Claude chat web, DeepSeek, Gemini, Copilot, Perplexity, Grok
"""

import json
import time
import re
from urllib.parse import quote_plus

import requests


class WebTools:
    def __init__(self, registry):
        self.registry = registry
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KAJUU.AI/1.0 (research assistant)",
        })

    def get_tools(self):
        return {
            "web_fetch": (self.web_fetch, "Fetch URL content", {
                "url": {"type": "string", "description": "URL to fetch"},
                "format": {"type": "string", "optional": True, "description": "Output format: markdown, text, html"},
                "timeout": {"type": "integer", "optional": True, "description": "Timeout in seconds"},
            }),
            "web_search": (self.web_search, "Search the web", {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "optional": True, "description": "Number of results"},
            }),
            "image_search": (self.image_search, "Search for images", {
                "query": {"type": "string", "description": "Search query"},
                "count": {"type": "integer", "optional": True, "description": "Number of images"},
            }),
            "url_context": (self.url_context, "Extract readable content from URL", {
                "url": {"type": "string", "description": "URL to extract"},
            }),
        }

    def web_fetch(self, url, format="markdown", timeout=30):
        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            if not resp.ok:
                return {"error": f"HTTP {resp.status_code}", "url": url}
            content = resp.text
            content_type = resp.headers.get("content-type", "")
            return {
                "url": url,
                "status": resp.status_code,
                "content_type": content_type,
                "content": content[:500000],
                "content_length": len(content),
            }
        except requests.Timeout:
            return {"error": "Request timed out", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}

    def web_search(self, query, num_results=8):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            resp = self.session.get(url, timeout=15)
            if not resp.ok:
                return {"error": f"Search failed: HTTP {resp.status_code}", "query": query}
            html = resp.text
            results = []
            for match in re.finditer(
                r'<a rel="nofollow" class="result__a" href="(.*?)">.*?<b>(.*?)</b>.*?<a class="result__snippet".*?>(.*?)</a>',
                html, re.DOTALL
            ):
                href = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
                results.append({"title": title, "url": href, "snippet": snippet})
                if len(results) >= num_results:
                    break
            return {"query": query, "results": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e), "query": query}

    def image_search(self, query, count=5):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' images')}"
            resp = self.session.get(url, timeout=15)
            if not resp.ok:
                return {"error": f"Search failed: HTTP {resp.status_code}"}
            html = resp.text
            images = []
            for match in re.finditer(r'<img[^>]+src="(https?://[^"]+)"', html):
                src = match.group(1)
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                    images.append({"url": src})
                    if len(images) >= count:
                        break
            return {"query": query, "images": images, "count": len(images)}
        except Exception as e:
            return {"error": str(e), "query": query}

    def url_context(self, url):
        return self.web_fetch(url, format="text")

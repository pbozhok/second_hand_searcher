"""
Review search - finds reviews for products from various sources.
"""

import asyncio

import httpx
from ddgs import DDGS
from rich.console import Console

import config
from core.logging import get_logger

console = Console()
logger = get_logger(__name__, module_name="reviewers.search")


class ReviewSearcher:
    """Searches for reviews from various sources (DuckDuckGo, SerpAPI)."""

    async def search_duckduckgo(self, model: str, max_results: int = 3) -> list[dict]:
        """
        Search for reviews using the duckduckgo-search library.
        Targets review-rich sites: Reddit, Notebookcheck, RTINGS, Wirecutter, GSMArena.
        """
        query = (
            f"{model} review site:reddit.com OR site:notebookcheck.net "
            "OR site:rtings.com OR site:wirecutter.com OR site:gsmarena.com"
        )

        def _run() -> list[dict]:
            try:
                with DDGS() as ddgs:
                    raw = ddgs.text(query, max_results=max_results)
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                    for r in (raw or [])
                    if r.get("title")
                ]
            except Exception as e:
                console.print(f"[red]DuckDuckGo search error for '{model}': {e}[/red]")
                return []

        return await asyncio.to_thread(_run)

    async def search_serpapi(self, model: str, max_results: int = 3) -> list[dict]:
        """
        SerpAPI search (requires SERPAPI_KEY env var).
        Free tier: 100 searches/month.
        """
        query = f"{model} review"
        url = "https://serpapi.com/search"
        results = []

        async with httpx.AsyncClient(timeout=6) as s:
            try:
                resp = await s.get(url, params={
                    "q": query,
                    "api_key": config.SERPAPI_KEY,
                    "num": max_results,
                })
                data = resp.json()

                for r in data.get("organic_results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "url": r.get("link", ""),
                    })
            except Exception as e:
                console.print(f"[red]SerpAPI error for '{model}': {e}[/red]")

        return results

    async def search_reviews(self, model: str) -> list[dict]:
        """
        Route to SerpAPI if key is available, otherwise DuckDuckGo.
        """
        if config.SERPAPI_KEY:
            return await self.search_serpapi(model)
        return await self.search_duckduckgo(model)

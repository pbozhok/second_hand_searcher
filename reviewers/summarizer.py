"""
Review summarizer - generates summaries of product reviews.
"""

import asyncio
from typing import Any

from rich.console import Console

from models import Listing
from llm import LLMClient
from utils import extract_json
from reviewers.search import ReviewSearcher

console = Console()


class ReviewSummarizer:
    """Generates summaries of product reviews."""
    
    def __init__(self, llm_client: LLMClient, debug: bool = False):
        """
        Initialize the summarizer.
        
        Args:
            llm_client: The LLM client to use for summarization
            debug: Whether to print debug information
        """
        self.llm_client = llm_client
        self.debug = debug
        self.searcher = ReviewSearcher()
    
    async def search_reviews_for_models(self, listings: list[Listing]) -> dict[str, list[dict]]:
        """
        Search reviews for each unique product model only once.
        Returns a dict mapping model → list of review dicts.
        
        Args:
            listings: List of listings to get unique models from
            
        Returns:
            Dictionary mapping model names to review lists
        """
        # Get unique models (preserving order)
        seen = set()
        unique_models = []
        for listing in listings:
            if listing.product_model and listing.product_model not in seen:
                unique_models.append(listing.product_model)
                seen.add(listing.product_model)
        
        if not unique_models:
            return {}
        
        console.print(f"  [dim]Searching reviews for {len(unique_models)} unique model(s): {', '.join(unique_models)}[/dim]")
        
        # Search for each model concurrently
        results = await asyncio.gather(*[self.searcher.search_reviews(model) for model in unique_models])
        
        # Map model → reviews
        reviews_cache = dict(zip(unique_models, results))
        
        if self.debug:
            for model, reviews in reviews_cache.items():
                console.print(f"  [dim]  → {model}: {len(reviews)} review(s)[/dim]")
        
        return reviews_cache

    async def generate_summary_for_model(self, model: str, raw_reviews: list[dict]) -> dict[str, Any]:
        """
        Generate a summary for a specific model's reviews.
        
        Args:
            model: The product model name
            raw_reviews: List of review dictionaries
            
        Returns:
            Dictionary with summary and links
        """
        if not raw_reviews:
            return {"summary": "No reviews found.", "links": []}
        
        review_links = [r["url"] for r in raw_reviews if r.get("url")]
        
        review_text = "\n\n".join(
            f"Source: {r['title']}\n{r['snippet']}" for r in raw_reviews
        )

        prompt = f"""Based on the review excerpts below for "{model}",
write a 2-3 sentence summary covering:
1. Key strengths
2. Main weaknesses
3. Who it is best suited for

Be concise and factual. Do not invent information not present in the excerpts.

Return ONLY a JSON object:
{{"summary": "your summary here"}}

Review excerpts:
{review_text}"""

        try:
            raw    = await self.llm_client.chat(prompt, temperature=0.2)
            parsed = extract_json(raw)
            if isinstance(parsed, dict):
                summary = parsed.get("summary", "Summary unavailable.")
            else:
                summary = "Summary unavailable."
        except Exception as e:
            summary = f"Error generating summary: {e}"
        
        return {"summary": summary, "links": review_links}

    async def aggregate_reviews(self, listings: list[Listing]) -> None:
        """
        Search reviews per unique model, generate summaries, then assign to listings.
        
        Args:
            listings: List of listings to aggregate reviews for
        """
        console.print("[bold cyan]Step 4: Aggregating reviews...[/bold cyan]")
        
        # Search for reviews once per unique model
        reviews_cache = await self.search_reviews_for_models(listings)
        
        # Generate summaries once per unique model
        summary_cache = {}
        unique_models = list(dict.fromkeys(l.product_model for l in listings if l.product_model))
        
        for model in unique_models:
            summary_cache[model] = await self.generate_summary_for_model(model, reviews_cache.get(model, []))
        
        # Assign cached summaries to all listings with that model
        for listing in listings:
            if listing.product_model in summary_cache:
                summary_data = summary_cache[listing.product_model]
                listing.review_summary = summary_data["summary"]
                listing.review_links = summary_data["links"]
        
        console.print(f"  Done for {len(listings)} listings ({len(unique_models)} unique model(s))\n")

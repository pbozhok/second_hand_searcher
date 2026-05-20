"""
LLM filter - LLM-based relevance filtering for listings.
"""

import asyncio
import json
import random

import httpx
from rich.console import Console

from models import Listing
from llm import LLMClient
from utils import extract_json
import config

console = Console()


class LLMFilter:
    """LLM-based relevance filtering using Gemini or Mistral."""
    
    def __init__(self, llm_client: LLMClient, debug: bool = False):
        """
        Initialize the filter.
        
        Args:
            llm_client: The LLM client to use for filtering
            debug: Whether to print debug information
        """
        self.llm_client = llm_client
        self.debug = debug
    
    async def filter_listings(
        self,
        listings: list[Listing],
        user_query: str,
        batch_size: int = config.BATCH_SIZE,
        delay_between_batches: float = config.DELAY_BETWEEN_BATCHES,
        max_retries: int = config.MAX_RETRIES,
    ) -> list[Listing]:
        """
        Filters listings for relevance using LLM.
        Processes batches sequentially to avoid rate limits.
        
        Args:
            listings: List of listings to filter
            user_query: The user's search query
            batch_size: Number of items per batch
            delay_between_batches: Delay between batches in seconds
            max_retries: Maximum number of retries per batch
            
        Returns:
            Filtered list of relevant listings
        """
        async def judge_batch(batch: list[Listing]) -> None:
            items_json = json.dumps(
                [
                    {"id": i, "title": listing.title, "description": listing.description[:400]}
                    for i, listing in enumerate(batch)
                ],
                ensure_ascii=False,
            )

            prompt = f"""You are a shopping assistant. The user is looking for: "{user_query}"

Below is a JSON list of second-hand listings. For each one decide:
- relevant: true or false
- reason: 2-3 words maximum explaining why (e.g., "not phone", "wrong brand", "accessory only")

A listing is relevant if it matches the user's query closely in terms of product type, brand, or features.
Eg. if the user is looking for "iPhone 12 with good camera", a listing titled "iPhone 12 Pro Max - Excellent Camera" would be relevant, while "iPhone 12 case" would be not relevant with reason "case only".

Return ONLY a JSON object in this exact format:
{{"results": [{{"id": 0, "relevant": true, "reason": "..."}}]}}

Listings:
{items_json}"""

            for attempt in range(max_retries):
                try:
                    raw_response = await self.llm_client.chat(prompt)
                    parsed_response = extract_json(raw_response)

                    if isinstance(parsed_response, dict):
                        verdicts = parsed_response.get("results", [])
                    elif isinstance(parsed_response, list):
                        verdicts = parsed_response
                    else:
                        verdicts = []

                    for verdict in verdicts:
                        idx = verdict.get("id")
                        if idx is not None and 0 <= idx < len(batch):
                            batch[idx].relevant = verdict.get("relevant", False)
                            batch[idx].relevance_reason = verdict.get("reason", "")
                            # Print discarded listings immediately
                            if not batch[idx].relevant and batch[idx].relevance_reason:
                                console.print(f"  [red]✗ {batch[idx].title}: {batch[idx].relevance_reason}[/red]")

                    return

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        wait_time = (2 ** attempt) + random.uniform(1, 3)
                        console.print(f"[yellow]Rate limited. Waiting {wait_time:.1f}s before retrying...[/yellow]")
                        await asyncio.sleep(wait_time)
                    else:
                        console.print(f"[red]HTTP error: {e}[/red]")
                        break

                except Exception as e:
                    if attempt == max_retries - 1:
                        console.print(f"[red]Filter batch error: {e} — keeping batch as-is[/red]")
                        for listing in batch:
                            listing.relevant = True
                    else:
                        wait_time = (2 ** attempt) + random.uniform(1, 3)
                        console.print(f"[yellow]Retrying in {wait_time:.1f}s due to error: {e}[/yellow]")
                        await asyncio.sleep(wait_time)

        total_batches = (len(listings) + batch_size - 1) // batch_size
        total_discarded = 0

        for i in range(0, len(listings), batch_size):
            batch_num = i // batch_size + 1
            batch = listings[i:i + batch_size]
            console.print(f"Judging batch {batch_num}/{total_batches} ({len(batch)} items)...")
            await judge_batch(batch)

            # Count discarded in this batch
            batch_discarded = sum(1 for l in batch if not l.relevant)
            total_discarded += batch_discarded

            if i + batch_size < len(listings):
                await asyncio.sleep(delay_between_batches)

        if not any(listing.relevant for listing in listings):
            console.print("[yellow]No relevant listings found. Marking all as relevant as fallback.[/yellow]")
            for listing in listings:
                listing.relevant = True
                listing.relevance_reason = "Fallback: No relevant listings identified by the model."

        relevant_listings = [listing for listing in listings if listing.relevant]
        if total_discarded > 0:
            console.print(f"[bold yellow]{total_discarded} listings discarded[/bold yellow]")
        console.print(f"[bold green]{len(relevant_listings)} relevant listings kept[/bold green]\n")
        return relevant_listings

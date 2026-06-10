"""
Description fetcher - fetches full descriptions from product pages.

Implements BaseProcessor for the modular pipeline.
"""

import json
import re
import asyncio
from typing import List, Dict, Any

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

from models import Listing
from core.module import ModuleType
from core.logging import get_logger
from processors.base import BaseProcessor
import config

console = Console()
logger = get_logger(__name__, module_name="processors.description_fetcher")


class DescriptionFetcher(BaseProcessor):
    """Fetches descriptions from product pages for different platforms."""
    
    name = "description-fetcher"
    module_type = ModuleType.PROCESSOR
    version = "1.0.0"
    
    def __init__(self, debug: bool = False):
        """
        Initialize the fetcher.
        
        Args:
            debug: Whether to print debug information
        """
        super().__init__()
        self.debug = debug
        self.headers = config.HEADERS
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize with configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if initialization succeeded
        """
        self._initialized = True
        self.debug = config.get("debug", False)
        logger.info("DescriptionFetcher initialized")
        return True
    
    def validate(self) -> bool:
        """
        Validate the module is properly configured.
        
        Returns:
            True if valid
        """
        return self._initialized
    
    async def process(self, listings: List[Any], context: Dict[str, Any]) -> List[Any]:
        """
        Fetch descriptions for all listings.

        Args:
            listings: List of listings to process
            context: Additional context

        Returns:
            Processed list of listings with descriptions fetched
        """
        if not listings:
            return listings

        # Skip listings that already have a description (e.g. DBA fetches it during scraping)
        needs_fetch = [
            l for l in listings
            if hasattr(l, 'platform') and not (l.description and l.description not in ("", "..."))
        ]

        logger.info("Fetching descriptions", extra={"listing_count": len(needs_fetch), "skipped": len(listings) - len(needs_fetch)})

        if not needs_fetch:
            return listings

        sem = asyncio.Semaphore(20)
        async with httpx.AsyncClient(
            headers=self.headers, follow_redirects=True, timeout=10
        ) as client:
            tasks = []
            for listing in needs_fetch:
                if listing.platform == "DBA":
                    tasks.append(self._fetch_description_dba(listing, client, sem))
                elif listing.platform == "Tradera":
                    tasks.append(self._fetch_description_tradera(listing, client, sem))
                elif listing.platform == "Vinted":
                    tasks.append(self._fetch_description_vinted(listing, client, sem))
            if tasks:
                await asyncio.gather(*tasks)

        return listings

    async def _fetch_description_dba(self, listing: Listing, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> None:
        """Fetch description from DBA product page."""
        async with sem:
            try:
                resp = await client.get(listing.url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                text = ""
                script = soup.find("script", type="application/ld+json")
                if script:
                    try:
                        data = json.loads(script.string)
                        text = data.get("description", "") or ""
                    except (json.JSONDecodeError, AttributeError):
                        pass

                if not text or len(text) <= 10:
                    desc_elem = soup.find("div", class_=re.compile(r"description|excerpt|summary", re.I))
                    if desc_elem:
                        text = desc_elem.get_text(strip=True)
                    elif not text:
                        desc_elem = soup.find(["p", "div"], attrs={"data-testid": re.compile(r"description", re.I)})
                        if desc_elem:
                            text = desc_elem.get_text(strip=True)

                if not listing.date_posted:
                    date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|oprettet|dato", re.I))
                    if date_el:
                        date_text = re.sub(r'^(Oprettet|Posted|Created|Dato):?\s*', '', date_el.get_text(strip=True), flags=re.I)
                        if date_text and len(date_text) < 50:
                            listing.date_posted = date_text
                    else:
                        time_el = soup.find("time")
                        if time_el:
                            listing.date_posted = time_el.get("datetime", "").split("T")[0]

                if text and len(text) > 10:
                    listing.description = text[:500]
                    if self.debug:
                        console.print(f"  [dim]DBA desc: {text[:100]}...[/dim]")
            except Exception as e:
                if self.debug:
                    console.print(f"  [dim]DBA desc fetch error: {e}[/dim]")
                logger.error("DBA description fetch error", extra={"error": str(e), "url": listing.url})

    async def _fetch_description_tradera(self, listing: Listing, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> None:
        """Fetch description from Tradera product page."""
        async with sem:
            try:
                resp = await client.get(listing.url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                desc_elem = soup.find("div", class_=re.compile(r"description|item.*desc", re.I))
                if not desc_elem:
                    heading = soup.find(["h2", "h3"], string=re.compile(r"description", re.I))
                    if heading:
                        desc_elem = heading.find_next("div", class_=re.compile(r"content|text|desc", re.I))

                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 10:
                        listing.description = text[:500]
                        if self.debug:
                            console.print(f"  [dim]Tradera desc: {text[:100]}...[/dim]")

                if not listing.date_posted:
                    date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|skapat|upp skapad", re.I))
                    if date_el:
                        date_text = re.sub(r'^(Publicerad|Skapad|Posted|Created):?\s*', '', date_el.get_text(strip=True), flags=re.I)
                        if date_text and len(date_text) < 50:
                            listing.date_posted = date_text
                    else:
                        time_el = soup.find("time")
                        if time_el:
                            listing.date_posted = time_el.get("datetime", "").split("T")[0]
            except Exception as e:
                if self.debug:
                    console.print(f"  [dim]Tradera desc fetch error: {e}[/dim]")
                logger.error("Tradera description fetch error", extra={"error": str(e), "url": listing.url})

    async def _fetch_description_vinted(self, listing: Listing, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> None:
        """Fetch description from Vinted product page."""
        async with sem:
            try:
                resp = await client.get(listing.url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                text = ""
                script = soup.find("script", type="application/ld+json")
                if script:
                    try:
                        data = json.loads(script.string)
                        text = data.get("description", "") or ""
                        if not listing.date_posted:
                            date_str = data.get("datePosted", "") or data.get("datePublished", "") or data.get("dateCreated", "")
                            if date_str:
                                listing.date_posted = date_str.split("T")[0]
                    except (json.JSONDecodeError, AttributeError):
                        pass

                if not text or len(text) <= 10:
                    desc_elem = soup.find("div", attrs={"data-testid": re.compile(r"item.*description", re.I)})
                    if desc_elem:
                        text = desc_elem.get_text(strip=True)
                    elif not text:
                        desc_elem = soup.find("div", class_=re.compile(r"description", re.I))
                        if desc_elem:
                            text = desc_elem.get_text(strip=True)

                if not listing.date_posted:
                    date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|oprettet|dato", re.I))
                    if date_el:
                        date_text = re.sub(r'^(Oprettet|Posted|Created|Dato):?\s*', '', date_el.get_text(strip=True), flags=re.I)
                        if date_text and len(date_text) < 50:
                            listing.date_posted = date_text
                    else:
                        time_el = soup.find("time")
                        if time_el:
                            listing.date_posted = time_el.get("datetime", "").split("T")[0]

                if text and len(text) > 10:
                    listing.description = text[:500]
                    if self.debug:
                        console.print(f"  [dim]Vinted desc: {text[:100]}...[/dim]")
            except Exception as e:
                if self.debug:
                    console.print(f"  [dim]Vinted desc fetch error: {e}[/dim]")
                logger.error("Vinted description fetch error", extra={"error": str(e), "url": listing.url})

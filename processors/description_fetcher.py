"""
Description fetcher - fetches full descriptions from product pages.
"""

import re

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

from models import Listing
import config

console = Console()


class DescriptionFetcher:
    """Fetches descriptions from product pages for different platforms."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the fetcher.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
        self.headers = config.HEADERS
    
    async def fetch_description_dba(self, listing: Listing) -> None:
        """Fetch description from DBA product page."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(listing.url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Try to find description in various places
                desc_elem = soup.find("div", class_=re.compile(r"description|excerpt|summary", re.I))
                if not desc_elem:
                    desc_elem = soup.find(["p", "div"], attrs={"data-testid": re.compile(r"description", re.I)})
                
                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 10:
                        listing.description = text[:500]  # Limit to 500 chars
                        if self.debug:
                            console.print(f"  [dim]DBA desc: {text[:100]}...[/dim]")
        except Exception as e:
            if self.debug:
                console.print(f"  [dim]DBA desc fetch error: {e}[/dim]")

    async def fetch_description_tradera(self, listing: Listing) -> None:
        """Fetch description from Tradera product page."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(listing.url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Look for description sections
                desc_elem = soup.find("div", class_=re.compile(r"description|item.*desc", re.I))
                if not desc_elem:
                    # Try finding a section with "Description" heading
                    heading = soup.find(["h2", "h3"], string=re.compile(r"description", re.I))
                    if heading:
                        desc_elem = heading.find_next("div", class_=re.compile(r"content|text|desc", re.I))
                
                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 10:
                        listing.description = text[:500]
                        if self.debug:
                            console.print(f"  [dim]Tradera desc: {text[:100]}...[/dim]")
        except Exception as e:
            if self.debug:
                console.print(f"  [dim]Tradera desc fetch error: {e}[/dim]")

    async def fetch_description_vinted(self, listing: Listing) -> None:
        """Fetch description from Vinted product page if not already present."""
        try:
            if listing.description and listing.description != "...":
                # Already has description
                return
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(listing.url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Vinted typically has description in a specific section
                desc_elem = soup.find("div", attrs={"data-testid": re.compile(r"item.*description", re.I)})
                if not desc_elem:
                    desc_elem = soup.find("div", class_=re.compile(r"description", re.I))
                
                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 10:
                        listing.description = text[:500]
                        if self.debug:
                            console.print(f"  [dim]Vinted desc: {text[:100]}...[/dim]")
        except Exception as e:
            if self.debug:
                console.print(f"  [dim]Vinted desc fetch error: {e}[/dim]")

    async def fetch_descriptions(self, listings: list[Listing]) -> None:
        """
        Fetch descriptions from product pages for all listings.
        
        Args:
            listings: List of listings to fetch descriptions for
        """
        console.print("[bold cyan]Step 4.5: Fetching descriptions for relevant items...[/bold cyan]")
        
        tasks = []
        for listing in listings:
            if listing.platform == "DBA":
                tasks.append(self.fetch_description_dba(listing))
            elif listing.platform == "Tradera":
                tasks.append(self.fetch_description_tradera(listing))
            elif listing.platform == "Vinted":
                tasks.append(self.fetch_description_vinted(listing))
        
        if tasks:
            import asyncio
            await asyncio.gather(*tasks)
            console.print(f"  Done for {len(listings)} listings\n")
        else:
            console.print("  No listings to fetch descriptions for\n")

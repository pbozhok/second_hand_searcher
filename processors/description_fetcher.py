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
                
                text = ""
                
                # Try JSON-LD script tag first (DBA serves description here)
                script = soup.find("script", type="application/ld+json")
                if script:
                    import json
                    try:
                        data = json.loads(script.string)
                        text = data.get("description", "") or ""
                    except (json.JSONDecodeError, AttributeError):
                        pass
                
                # Fallback to div-based selectors
                if not text or len(text) <= 10:
                    desc_elem = soup.find("div", class_=re.compile(r"description|excerpt|summary", re.I))
                    if desc_elem:
                        text = desc_elem.get_text(strip=True)
                    elif not text:
                        desc_elem = soup.find(["p", "div"], attrs={"data-testid": re.compile(r"description", re.I)})
                        if desc_elem:
                            text = desc_elem.get_text(strip=True)
                
                # Try to extract date from the page
                if not listing.date_posted:
                    date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|oprettet|dato", re.I))
                    if date_el:
                        import re
                        date_text = date_el.get_text(strip=True)
                        date_text = re.sub(r'^(Oprettet|Posted|Created|Dato):?\s*', '', date_text, flags=re.I)
                        if date_text and len(date_text) < 50:
                            listing.date_posted = date_text
                    else:
                        time_el = soup.find("time")
                        if time_el:
                            listing.date_posted = time_el.get("datetime", "").split("T")[0]
                
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
            
            # Try to extract date from the page
            if not listing.date_posted:
                import re
                date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|skapat|upp skapad", re.I))
                if date_el:
                    date_text = date_el.get_text(strip=True)
                    date_text = re.sub(r'^(Publicerad|Skapad|Posted|Created):?\s*', '', date_text, flags=re.I)
                    if date_text and len(date_text) < 50:
                        listing.date_posted = date_text
                else:
                    time_el = soup.find("time")
                    if time_el:
                        listing.date_posted = time_el.get("datetime", "").split("T")[0]
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
                
                text = ""
                
                # Try JSON-LD script tag first (Vinted serves description here)
                script = soup.find("script", type="application/ld+json")
                if script:
                    import json
                    try:
                        data = json.loads(script.string)
                        text = data.get("description", "") or ""
                        # Try to get date from JSON-LD
                        if not listing.date_posted:
                            date_str = data.get("datePosted", "") or data.get("datePublished", "") or data.get("dateCreated", "")
                            if date_str:
                                listing.date_posted = date_str.split("T")[0]
                    except (json.JSONDecodeError, AttributeError):
                        pass
                
                # Fallback to div-based selectors
                if not text or len(text) <= 10:
                    desc_elem = soup.find("div", attrs={"data-testid": re.compile(r"item.*description", re.I)})
                    if desc_elem:
                        text = desc_elem.get_text(strip=True)
                    elif not text:
                        desc_elem = soup.find("div", class_=re.compile(r"description", re.I))
                        if desc_elem:
                            text = desc_elem.get_text(strip=True)
                
                # Try to extract date from the page
                if not listing.date_posted:
                    import re
                    date_el = soup.find(["span", "div", "time"], class_=re.compile(r"date|time|posted|published|oprettet|dato", re.I))
                    if date_el:
                        date_text = date_el.get_text(strip=True)
                        date_text = re.sub(r'^(Oprettet|Posted|Created|Dato):?\s*', '', date_text, flags=re.I)
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

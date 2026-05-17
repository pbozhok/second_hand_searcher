"""
DBA scraper - for dba.dk second-hand listings.
"""

import re
import urllib.parse

import httpx
from bs4 import BeautifulSoup
from rich.console import Console

from models import Listing
from scrapers.base import BaseScraper
import config

console = Console()


class DBAScraper(BaseScraper):
    """Scraper for DBA.dk recommerce listings."""
    
    platform = "DBA"
    
    async def scrape(self, query: str, max_results: int = 20) -> list[Listing]:
        """
        Scrape DBA listings using the recommerce URL structure.
        Search page: https://www.dba.dk/recommerce/forsale/search?q=...
        """
        url = f"https://www.dba.dk/recommerce/forsale/search?q={urllib.parse.quote_plus(query)}"
        listings = []

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=config.SCRAPER_TIMEOUT) as s:
            try:
                resp = await s.get(url)
                soup = BeautifulSoup(resp.text, "html.parser")

                # Try multiple selector strategies
                cards = soup.select('a[href*="/recommerce/forsale/item/"]')
                
                self.log_debug(f"[blue]DBA: Found {len(cards)} cards with primary selector[/blue]")
                
                # If no cards found, try alternative selectors
                if not cards:
                    # Look for any anchor tags with recommerce item URLs
                    cards = [a for a in soup.find_all('a') if '/recommerce/forsale/item/' in a.get('href', '')]
                    self.log_debug(f"[blue]DBA: Found {len(cards)} cards with alternative selector[/blue]")
                
                cards = cards[:max_results]

                seen_urls = set()
                for i, card in enumerate(cards):
                    href = card.get("href", "")
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # Title: get the card's text content
                    title = card.get_text(strip=True)
                    
                    self.log_debug(f"[dim]DBA card {i} text: '{title}'[/dim]")
                    
                    # If link text is empty, look at the parent container
                    if not title:
                        parent = card.parent
                        if parent:
                            # Try to find title in nearby elements
                            title_el = parent.select_one('h2, h3, h4, [class*="title"], [class*="name"], [data-testid*="title"]')
                            if title_el:
                                title = title_el.get_text(strip=True)
                                self.log_debug(f"[dim]DBA found in parent: '{title}'[/dim]")
                            else:
                                # Try to get all text from parent (more aggressive)
                                title = parent.get_text(strip=True)[:200]
                                self.log_debug(f"[dim]DBA from parent text: '{title[:80]}'[/dim]")
                    
                    # If still no title, extract from URL
                    if not title or len(title) < 2:
                        match = re.search(r'/item/(\d+)', href)
                        if match:
                            title = f"DBA Item {match.group(1)}"
                        else:
                            continue
                    
                    # Clean title if it contains price info
                    title_parts = re.split(r'\d+\s*kr|kr\.|dkk', title, flags=re.IGNORECASE)
                    title = title_parts[0].strip() if title_parts else title
                    
                    # Price: first look within the card itself
                    price_el = card.find(
                        lambda tag: tag.name in ("span", "div", "p")
                        and "kr" in tag.get_text().lower()
                        and len(tag.get_text(strip=True)) < 30
                    )
                    
                    # If not found in card, look in parent container
                    if not price_el and card.parent:
                        price_el = card.parent.find(
                            lambda tag: tag.name in ("span", "div", "p")
                            and "kr" in tag.get_text().lower()
                            and len(tag.get_text(strip=True)) < 30
                        )
                    
                    # If still not found, try a broader search
                    if not price_el:
                        search_area = card.parent if card.parent else card
                        for el in search_area.find_all(['span', 'div', 'p', 'strong', 'b']):
                            text = el.get_text(strip=True)
                            if re.search(r'\d+.*kr', text, re.IGNORECASE) and len(text) < 50:
                                price_el = el
                                self.log_debug(f"[blue]DBA broad price search found: {text}[/blue]")
                                break
                    
                    price_text = price_el.get_text(strip=True) if price_el else "0"
                    price = self.parse_price(price_text)
                    
                    if self.debug:
                        if price_el:
                            self.log_debug(f"[dim]DBA price: {price_text} -> {price}[/dim]")
                        else:
                            self.log_debug(f"[yellow]DBA no price found for {title}[/yellow]")

                    full_url = (
                        f"https://www.dba.dk{href}"
                        if href.startswith("/")
                        else href
                    )
                    
                    # Description: try to extract from the card or parent
                    description = ""
                    if card.parent:
                        desc_el = card.parent.select_one('[class*="description"], [class*="excerpt"], [class*="summary"]')
                        if desc_el:
                            description = desc_el.get_text(strip=True)[:300]

                    # Date posted: try to extract from the card's article container
                    date_posted = ""
                    # Find the article ancestor which contains the date
                    article = card.find_parent('article')
                    if article:
                        article_text = article.get_text()
                        # Look for relative date patterns like "Nyt i dag", "2 dage", "8 t.", etc.
                        # t. = timer (hours), d. = dage (days)
                        date_match = re.search(r'(Nyt i (dag|g\u00e5r)|(\d+)\s*(dage?|d\.|uge(r)?|m\u00e5ned(er)?|t\.)|Oprettet\s*:?\s*(\S+))', article_text, re.I)
                        if date_match:
                            date_posted = date_match.group(0).strip()
                            # Clean up the date text
                            date_posted = re.sub(r'\s+', ' ', date_posted)
                        else:
                            # Try looking for date elements
                            date_el = article.select_one('[class*="date"], [class*="time"], [class*="posted"], [class*="published"], [class*="oprettet"]')
                            if date_el:
                                date_posted = date_el.get_text(strip=True)
                            else:
                                # Try time tag
                                time_el = article.find("time")
                                if time_el:
                                    date_posted = time_el.get("datetime", time_el.get_text(strip=True))
                    elif card.parent:
                        # Fallback to parent
                        date_el = card.parent.select_one('[class*="date"], [class*="time"], [class*="posted"], [class*="published"], [class*="oprettet"]')
                        if date_el:
                            date_posted = date_el.get_text(strip=True)
                        else:
                            time_el = card.parent.find("time")
                            if time_el:
                                date_posted = time_el.get("datetime", time_el.get_text(strip=True))

                    listings.append(Listing(
                        title=title,
                        price=price,
                        currency="DKK",
                        url=full_url,
                        description=description,
                        platform=self.platform,
                        date_posted=date_posted,
                    ))

            except Exception as e:
                console.print(f"[red]DBA error: {e}[/red]")

        console.print(f"[green]DBA:[/green] {len(listings)} listings found")
        return listings

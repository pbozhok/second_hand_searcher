"""
Keyword filter - simple keyword-based filtering for listings.
"""

from rich.console import Console

from models import Listing

console = Console()


class KeywordFilter:
    """Simple keyword-based filtering for relevance checking."""
    
    async def filter_listings(self, listings: list[Listing], user_query: str) -> list[Listing]:
        """
        Simple keyword-based filtering fallback.
        Keeps listings that contain query keywords in title or description.
        
        Args:
            listings: List of listings to filter
            user_query: The user's search query
            
        Returns:
            Filtered list of relevant listings
        """
        keywords = user_query.lower().split()
        relevant_listings = []
        discarded_count = 0
        
        for listing in listings:
            text = (listing.title + " " + listing.description).lower()
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in text)
            
            if matches >= max(1, len(keywords) // 2):  # At least half the keywords
                listing.relevant = True
                listing.relevance_reason = f"Contains {matches}/{len(keywords)} search keywords"
                relevant_listings.append(listing)
            else:
                listing.relevant = False
                listing.relevance_reason = f"Only {matches}/{len(keywords)} keywords"
                console.print(f"  [red]✗ {listing.title}: {listing.relevance_reason}[/red]")
                discarded_count += 1
        
        if discarded_count > 0:
            console.print(f"[bold yellow]{discarded_count} listings discarded[/bold yellow]")
        console.print(f"[bold green]{len(relevant_listings)} relevant listings kept (keyword-based)[/bold green]\n")
        
        if not relevant_listings:
            console.print("[yellow]No keyword matches found. Including all listings.[/yellow]\n")
            for listing in listings:
                listing.relevant = True
                listing.relevance_reason = "Fallback: included due to no keyword matches"
            return listings
        
        return relevant_listings

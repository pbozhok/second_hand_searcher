"""
Price converter - handles currency conversion for listings.
"""

from rich.console import Console

from models import Listing
import config

console = Console()


class PriceConverter:
    """Handles currency conversion for listings."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the converter.
        
        Args:
            debug: Whether to print debug information
        """
        self.debug = debug
        self.exchange_rates = config.EXCHANGE_RATES
    
    async def convert_prices(self, listings: list[Listing], target_currency: str) -> None:
        """
        Convert all listing prices to target currency.
        
        Args:
            listings: List of listings to convert
            target_currency: The target currency code (EUR, DKK, SEK)
        """
        if not listings:
            return
        
        # Check if any conversion is needed
        needs_conversion = any(l.currency != target_currency for l in listings)
        if needs_conversion:
            console.print(f"[bold cyan]Converting prices to {target_currency}...[/bold cyan]")
            
            for listing in listings:
                if listing.currency != target_currency:
                    # Convert from listing currency to EUR first, then to target
                    source_rate = self.exchange_rates.get(listing.currency, 1.0)
                    target_rate = self.exchange_rates.get(target_currency, 1.0)
                    original_price = listing.price
                    listing.price = round(listing.price / source_rate * target_rate, 2)
                    
                    if self.debug:
                        console.print(f"  [dim]{listing.title}: {original_price} {listing.currency} → {listing.price} {target_currency}[/dim]")
                    
                    listing.currency = target_currency
            
            console.print("")

"""
Base scraper class with common functionality for all platform scrapers.
"""

from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

from models import Listing
from utils import parse_price
import config

console = Console()


class BaseScraper(ABC):
    """Abstract base class for platform-specific scrapers."""
    
    platform: str = "Unknown"
    
    def __init__(self, headers: dict = None, debug: bool = False):
        """
        Initialize the scraper.
        
        Args:
            headers: HTTP headers to use for requests
            debug: Whether to print debug information
        """
        self.headers = headers or config.HEADERS
        self.debug = debug
    
    @abstractmethod
    async def scrape(self, query: str, max_results: int = 20) -> list[Listing]:
        """
        Scrape listings for the given query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of Listing objects
        """
        pass
    
    def log_debug(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            console.print(message)
    
    @staticmethod
    def parse_price(text: str) -> float:
        """Parse price from text (delegates to utils)."""
        return parse_price(text)

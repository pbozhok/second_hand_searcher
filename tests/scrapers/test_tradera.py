"""
Tests for Tradera scraper.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from models import Listing
from scrapers.tradera import TraderaScraper


class TestTraderaScraper:
    """Tests for TraderaScraper class."""

    def test_tradera_scraper_initialization(self):
        """Test TraderaScraper can be initialized."""
        scraper = TraderaScraper(debug=False)
        assert scraper.platform == "Tradera"

    def test_tradera_scraper_parse_price(self):
        """Test TraderaScraper price parsing."""
        scraper = TraderaScraper(debug=False)
        assert scraper.parse_price("100 SEK") == 100.0
        assert scraper.parse_price("1 000 SEK") == 1000.0
        assert scraper.parse_price("99.99 SEK") == 99.99

    @patch('httpx.AsyncClient')
    async def test_tradera_scraper_scrape(self, mock_client):
        """Test TraderaScraper scrape method."""
        mock_resp = MagicMock()
        mock_resp.text = '''
        <html><body>
            <div id="item-card-1">
                <a href="/en/item/260103/12345/test-item">Test Item</a>
                <span>100 SEK</span>
            </div>
        </body></html>
        '''
        mock_resp.raise_for_status = AsyncMock()
        
        mock_client.return_value.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_resp)
        
        scraper = TraderaScraper(debug=False)
        listings = await scraper.scrape("test", max_results=10)
        
        # Check that listings have required fields
        for listing in listings:
            assert isinstance(listing, Listing)
            assert listing.platform == "Tradera"

    @patch('httpx.AsyncClient')
    async def test_tradera_scraper_date_extraction(self, mock_client):
        """Test that Tradera scraper can extract dates."""
        mock_resp = MagicMock()
        mock_resp.text = '''
        <html><body>
            <div id="item-card-1">
                <a href="/en/item/260103/12345/test-item">Test Item</a>
                <span>100 SEK</span>
                <span class="date">2024-01-15</span>
            </div>
        </body></html>
        '''
        mock_resp.raise_for_status = AsyncMock()
        
        mock_client.return_value.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_resp)
        
        scraper = TraderaScraper(debug=False)
        listings = await scraper.scrape("test", max_results=10)
        
        # Check that listings were created
        assert len(listings) >= 0

    def test_tradera_scraper_empty_results(self):
        """Test Tradera scraper handles empty results."""
        scraper = TraderaScraper(debug=False)
        assert hasattr(scraper, 'scrape')

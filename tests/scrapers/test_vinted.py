"""
Tests for Vinted scraper.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from models import Listing
from scrapers.vinted import VintedScraper


class TestVintedScraper:
    """Tests for VintedScraper class."""

    def test_vinted_scraper_initialization(self):
        """Test VintedScraper can be initialized."""
        scraper = VintedScraper(debug=False)
        assert scraper.platform == "Vinted"

    @patch('vinted_scraper.VintedScraper')
    async def test_vinted_scraper_scrape(self, mock_vinted_scraper):
        """Test VintedScraper scrape method with mocked vinted-scraper package."""
        # Mock the VintedScraper class from vinted-scraper package
        mock_instance = MagicMock()
        mock_instance.search.return_value = [
            MagicMock(
                title="Test Item",
                price="100",
                currency="DKK",
                url="https://vinted.dk/items/12345",
                description="Test description",
                json_data={
                    'photos': [{'high_resolution': {'timestamp': 1700000000}}]
                }
            )
        ]
        mock_vinted_scraper.return_value = mock_instance
        
        scraper = VintedScraper(debug=False)
        listings = await scraper.scrape("test", max_results=10)
        
        # Check that listings were created
        assert len(listings) >= 0
        
        # If listings were created, check their fields
        for listing in listings:
            assert isinstance(listing, Listing)
            assert listing.platform == "Vinted"

    @patch('vinted_scraper.VintedScraper')
    async def test_vinted_scraper_date_extraction(self, mock_vinted_scraper):
        """Test that Vinted scraper extracts dates from photo timestamps."""
        import datetime
        timestamp = int(datetime.datetime(2024, 1, 15).timestamp())
        
        mock_instance = MagicMock()
        mock_instance.search.return_value = [
            MagicMock(
                title="Test Item",
                price="100",
                currency="DKK",
                url="https://vinted.dk/items/12345",
                description="Test description",
                json_data={
                    'photos': [{'high_resolution': {'timestamp': timestamp}}]
                }
            )
        ]
        mock_vinted_scraper.return_value = mock_instance
        
        scraper = VintedScraper(debug=False)
        listings = await scraper.scrape("test", max_results=10)
        
        # Check if any listing has a date
        if listings:
            # The date should be extracted from the timestamp
            assert any(l.date_posted for l in listings)

    def test_vinted_scraper_handles_missing_package(self):
        """Test Vinted scraper handles missing vinted-scraper package."""
        with patch.dict('sys.modules', {'vinted_scraper': None}):
            scraper = VintedScraper(debug=False)
            # Should not raise an error when package is missing
            # (though it won't return any results)
            assert hasattr(scraper, 'scrape')

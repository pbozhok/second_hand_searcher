"""
Tests for base scraper class.
"""
import pytest
from scrapers.base import BaseScraper


class TestBaseScraper:
    """Tests for BaseScraper class."""

    def test_base_scraper_initialization(self):
        """Test BaseScraper can be initialized."""
        scraper = BaseScraper(debug=False)
        assert scraper.debug is False
        assert hasattr(scraper, 'platform')
        assert hasattr(scraper, 'headers')

    def test_base_scraper_debug_mode(self):
        """Test BaseScraper with debug mode."""
        scraper = BaseScraper(debug=True)
        assert scraper.debug is True

    def test_parse_price(self):
        """Test parse_price method."""
        scraper = BaseScraper(debug=False)
        assert scraper.parse_price("100") == 100.0
        assert scraper.parse_price("100 kr") == 100.0
        assert scraper.parse_price("1 000 DKK") == 1000.0
        assert scraper.parse_price("99.99") == 99.99

    def test_parse_price_edge_cases(self):
        """Test parse_price with edge cases."""
        scraper = BaseScraper(debug=False)
        assert scraper.parse_price("") == 0.0
        assert scraper.parse_price("free") == 0.0
        assert scraper.parse_price("N/A") == 0.0

    def test_log_debug(self):
        """Test log_debug method."""
        scraper = BaseScraper(debug=True)
        # Should not raise an error
        scraper.log_debug("Test message")

    def test_scrape_method_exists(self):
        """Test that scrape method exists (to be implemented by subclasses)."""
        scraper = BaseScraper(debug=False)
        assert hasattr(scraper, 'scrape')
        # The base implementation should return empty list
        import asyncio
        result = asyncio.run(scraper.scrape("test"))
        assert result == []

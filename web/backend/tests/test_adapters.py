"""
Unit tests for adapter functions.

Tests:
- T072: Unit test for adapters in web/backend/tests/test_adapters.py
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from models import Listing
from web.backend.models.schemas import (
    ItemResponse,
    ReviewResponse,
    SearchRequest,
    SearchResponse,
    ToggleStates,
)
from web.shared.adapters import (
    listing_to_item_response,
    review_summary_to_review_response,
    search_request_to_pipeline_config,
    create_search_response,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_listing():
    """Create a sample Listing object for testing."""
    listing = MagicMock(spec=Listing)
    listing.title = "Vintage Leather Jacket"
    listing.price = 99.99
    listing.currency = "EUR"
    listing.url = "https://dba.dk/item/12345"
    listing.platform = "DBA"
    listing.score = 0.95
    listing.score_reason = "High relevance: matches all keywords"
    listing.description = "Vintage leather jacket in excellent condition, size M"
    listing.date_posted = "2025-05-20"
    listing.images = ["https://dba.dk/images/12345.jpg"]
    listing.review_summary = "4.5/5 from 12 reviews"
    listing.review_links = ["https://reviews.example.com/12345"]
    return listing


@pytest.fixture
def sample_listing_no_reviews():
    """Create a sample Listing without reviews."""
    listing = MagicMock(spec=Listing)
    listing.title = "Simple Item"
    listing.price = 49.99
    listing.currency = "DKK"
    listing.url = "https://vinted.com/item/67890"
    listing.platform = "Vinted"
    listing.score = 0.85
    listing.score_reason = None
    listing.description = "Simple item description"
    listing.date_posted = "2025-05-19"
    listing.images = []
    listing.review_summary = ""
    listing.review_links = []
    return listing


# =============================================================================
# T072: Unit test for adapters
# =============================================================================

class TestListingToItemResponse:
    """Tests for listing_to_item_response adapter."""

    def test_converts_basic_fields(self, sample_listing):
        """Test that basic fields are converted correctly."""
        result = listing_to_item_response(sample_listing, index=0)

        assert isinstance(result, ItemResponse)
        assert result.title == "Vintage Leather Jacket"
        assert result.price == 99.99
        assert result.currency == "EUR"
        assert result.original_url == "https://dba.dk/item/12345"
        assert result.platform == "DBA"
        assert result.score == 0.95

    def test_generates_id_from_platform_and_index(self, sample_listing):
        """Test that ID is generated from platform and index."""
        result = listing_to_item_response(sample_listing, index=42)
        assert result.id == "dba-42"

    def test_handles_missing_image_url(self, sample_listing_no_reviews):
        """Test that missing images result in None image_url."""
        result = listing_to_item_response(sample_listing_no_reviews, index=0)
        assert result.image_url is None

    def test_handles_missing_description(self, sample_listing):
        """Test that None description is handled."""
        sample_listing.description = None
        result = listing_to_item_response(sample_listing, index=0)
        assert result.description is None

    def test_truncates_long_description(self, sample_listing):
        """Test that long descriptions are truncated to 500 chars."""
        sample_listing.description = "A" * 600
        result = listing_to_item_response(sample_listing, index=0)
        assert len(result.description) == 500

    def test_parses_date_correctly(self, sample_listing):
        """Test that date is parsed correctly from string."""
        result = listing_to_item_response(sample_listing, index=0)
        assert result.posted_date == "2025-05-20"

    def test_handles_invalid_date(self, sample_listing):
        """Test that invalid dates result in None."""
        sample_listing.date_posted = "invalid-date"
        result = listing_to_item_response(sample_listing, index=0)
        assert result.posted_date is None

    def test_handles_empty_date(self, sample_listing):
        """Test that None date is handled."""
        sample_listing.date_posted = None
        result = listing_to_item_response(sample_listing, index=0)
        assert result.posted_date is None

    def test_includes_score_reason(self, sample_listing):
        """Test that score_reason is included in response."""
        result = listing_to_item_response(sample_listing, index=0)
        assert result.score_reason == "High relevance: matches all keywords"

    def test_handles_missing_score_reason(self, sample_listing):
        """Test that None score_reason is handled."""
        sample_listing.score_reason = None
        result = listing_to_item_response(sample_listing, index=0)
        assert result.score_reason is None


class TestReviewSummaryToReviewResponse:
    """Tests for review_summary_to_review_response adapter."""

    def test_returns_none_for_empty_reviews(self):
        """Test that None is returned when no review data is available."""
        result = review_summary_to_review_response("", [], "test-id")
        assert result is None

    def test_parses_rating_from_summary(self):
        """Test that rating is parsed from summary text."""
        result = review_summary_to_review_response(
            "4.5/5 from 12 reviews",
            [],
            "test-id"
        )
        assert result is not None
        assert result.average_rating == 4.5

    def test_parses_review_count_from_summary(self):
        """Test that review count is parsed from summary text."""
        result = review_summary_to_review_response(
            "4.5/5 from 12 reviews",
            [],
            "test-id"
        )
        assert result is not None
        assert result.review_count == 12

    def test_detects_positive_sentiment(self):
        """Test that positive sentiment is detected."""
        result = review_summary_to_review_response(
            "excellent condition great quality",
            [],
            "test-id"
        )
        assert result is not None
        assert result.sentiment == "positive"

    def test_detects_negative_sentiment(self):
        """Test that negative sentiment is detected."""
        result = review_summary_to_review_response(
            "poor quality bad condition terrible",
            [],
            "test-id"
        )
        assert result is not None
        assert result.sentiment == "negative"

    def test_detects_neutral_sentiment(self):
        """Test that neutral sentiment is detected for neutral text."""
        result = review_summary_to_review_response(
            "average condition standard quality",
            [],
            "test-id"
        )
        assert result is not None
        assert result.sentiment == "neutral"

    def test_sets_source_from_links(self):
        """Test that source is set when review links are provided."""
        result = review_summary_to_review_response(
            "test",
            ["https://reviews.example.com/1"],
            "test-id"
        )
        assert result is not None
        assert result.source == "DuckDuckGo"

    def test_truncates_long_summary(self):
        """Test that long summaries are truncated."""
        long_summary = "A" * 1500
        result = review_summary_to_review_response(
            long_summary,
            [],
            "test-id"
        )
        assert result is not None
        assert len(result.summary) == 1000


class TestSearchRequestToPipelineConfig:
    """Tests for search_request_to_pipeline_config adapter."""

    def test_converts_all_fields(self):
        """Test that all fields are converted from request to config."""
        request = SearchRequest(
            query="test query",
            max_results=20,
            currency="DKK",
            use_filter=False,
            use_reviews=True,
            use_scoring=False,
            sort_by="price_asc"
        )

        result = search_request_to_pipeline_config(request)

        assert result["use_filter"] == False
        assert result["use_reviews"] == True
        assert result["use_scoring"] == False
        assert result["max_results"] == 20
        assert result["currency"] == "DKK"

    def test_uses_defaults_for_none_values(self):
        """Test that defaults are used for None values."""
        request = SearchRequest(query="test")

        result = search_request_to_pipeline_config(request)

        assert result["use_filter"] == True
        assert result["use_reviews"] == True
        assert result["use_scoring"] == True


class TestCreateSearchResponse:
    """Tests for create_search_response adapter."""

    def test_creates_response_with_results(self, sample_listing):
        """Test that response is created with converted results."""
        request = SearchRequest(
            query="test query",
            max_results=10,
            use_filter=True,
            use_reviews=True,
            use_scoring=True,
            sort_by="score"
        )

        listings = [sample_listing]

        result = create_search_response(
            query="test query",
            listings=listings,
            reviews={},
            request=request,
            total_results=1
        )

        assert isinstance(result, SearchResponse)
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.total_results == 1
        assert result.sort_by == "score"

    def test_sorts_by_score_descending(self, sample_listing):
        """Test that results are sorted by score descending by default."""
        listing2 = MagicMock(spec=Listing)
        listing2.title = "Item 2"
        listing2.price = 50.0
        listing2.currency = "EUR"
        listing2.url = "https://example.com/2"
        listing2.platform = "DBA"
        listing2.score = 0.98
        listing2.score_reason = None
        listing2.description = "Higher score"
        listing2.date_posted = "2025-05-21"
        listing2.images = []
        listing2.review_summary = ""
        listing2.review_links = []

        request = SearchRequest(
            query="test",
            sort_by="score"
        )

        listings = [sample_listing, listing2]

        result = create_search_response(
            query="test",
            listings=listings,
            reviews={},
            request=request,
            total_results=2
        )

        # Higher score should come first
        assert result.results[0].score >= result.results[1].score

    def test_sorts_by_price_ascending(self, sample_listing):
        """Test that results are sorted by price ascending when requested."""
        listing2 = MagicMock(spec=Listing)
        listing2.title = "Cheaper Item"
        listing2.price = 49.99
        listing2.currency = "EUR"
        listing2.url = "https://example.com/2"
        listing2.platform = "DBA"
        listing2.score = 0.95
        listing2.score_reason = None
        listing2.description = "Cheaper"
        listing2.date_posted = "2025-05-21"
        listing2.images = []
        listing2.review_summary = ""
        listing2.review_links = []

        request = SearchRequest(
            query="test",
            sort_by="price_asc"
        )

        listings = [sample_listing, listing2]

        result = create_search_response(
            query="test",
            listings=listings,
            reviews={},
            request=request,
            total_results=2
        )

        # Lower price should come first
        assert result.results[0].price <= result.results[1].price

    def test_handles_empty_listings(self):
        """Test that empty listings result in empty results."""
        request = SearchRequest(query="test")

        result = create_search_response(
            query="test",
            listings=[],
            reviews={},
            request=request,
            total_results=0
        )

        assert result.total_results == 0
        assert len(result.results) == 0

    def test_toggles_reflect_request(self, sample_listing):
        """Test that toggle states reflect request parameters."""
        request = SearchRequest(
            query="test",
            use_filter=False,
            use_reviews=False,
            use_scoring=True
        )

        result = create_search_response(
            query="test",
            listings=[sample_listing],
            reviews={},
            request=request,
            total_results=1
        )

        assert result.toggles.filtering == False
        assert result.toggles.reviewing == False
        assert result.toggles.scoring == True

    def test_timestamp_is_set(self, sample_listing):
        """Test that timestamp is set in response."""
        request = SearchRequest(query="test")

        before = datetime.utcnow().isoformat()
        result = create_search_response(
            query="test",
            listings=[sample_listing],
            reviews={},
            request=request,
            total_results=1
        )
        after = datetime.utcnow().isoformat()

        assert result.timestamp >= before
        assert result.timestamp <= after

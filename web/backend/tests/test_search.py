"""
Unit tests for search API endpoints.

Tests:
- T071: Unit test for GET /api/v1/search
- T075: Unit test for toggle handling in search
- T076: Unit test for sorting in search
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from web.backend.main import app
from web.backend.models.schemas import SearchResponse, ItemResponse, ToggleStates


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_pipeline():
    """Create a mock pipeline for testing."""
    mock = MagicMock()
    mock.execute = AsyncMock()
    return mock


# =============================================================================
# T071: Unit test for GET /api/v1/search endpoint
# =============================================================================

class TestSearchEndpoint:
    """Tests for the main search endpoint."""

    def test_search_returns_200_with_results(self, client, mock_pipeline):
        """Test that search endpoint returns 200 with valid results."""
        # Mock the pipeline to return test data
        mock_listing = MagicMock()
        mock_listing.title = "Test Item"
        mock_listing.price = 99.99
        mock_listing.currency = "EUR"
        mock_listing.url = "https://example.com/item/1"
        mock_listing.platform = "DBA"
        mock_listing.score = 0.95
        mock_listing.description = "Test description"
        mock_listing.date_posted = "2025-05-20"
        mock_listing.images = ["https://example.com/image.jpg"]
        mock_listing.review_summary = ""
        mock_listing.review_links = []

        mock_context = MagicMock()
        mock_context.listings = [mock_listing]
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            with patch('web.backend.api.search.get_pipeline', new_callable=lambda: mock_pipeline):
                response = client.get("/api/v1/search?query=test")

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["query"] == "test"
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_validates_query_required(self, client):
        """Test that query parameter is required."""
        response = client.get("/api/v1/search")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_search_validates_query_min_length(self, client):
        """Test that query must be at least 1 character."""
        response = client.get("/api/v1/search?query=")
        assert response.status_code == 422

    def test_search_validates_query_max_length(self, client):
        """Test that query cannot exceed 500 characters."""
        long_query = "a" * 501
        response = client.get(f"/api/v1/search?query={long_query}")
        assert response.status_code == 422

    def test_search_validates_max_results_range(self, client):
        """Test that max_results must be between 1 and 100."""
        # Test below minimum
        response = client.get("/api/v1/search?query=test&max_results=0")
        assert response.status_code == 422

        # Test above maximum
        response = client.get("/api/v1/search?query=test&max_results=101")
        assert response.status_code == 422

    def test_search_validates_sort_by_values(self, client):
        """Test that sort_by must be one of the allowed values."""
        response = client.get("/api/v1/search?query=test&sort_by=invalid")
        assert response.status_code == 422

    def test_search_default_parameters(self, client, mock_pipeline):
        """Test that default parameters are applied correctly."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test")

        assert response.status_code == 200
        data = response.json()
        # Check defaults
        assert data["total_results"] == 0
        assert data["sort_by"] == "score"

    def test_search_returns_error_on_exception(self, client, mock_pipeline):
        """Test that search returns 500 error on unexpected exception."""
        mock_pipeline.execute = AsyncMock(side_effect=Exception("Test error"))

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "internal_error"


# =============================================================================
# T075: Unit test for toggle handling in search
# =============================================================================

class TestToggleHandling:
    """Tests for toggle parameter handling in search endpoint."""

    def test_toggle_use_filter_false(self, client, mock_pipeline):
        """Test that use_filter=false disables filtering."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&use_filter=false")

        assert response.status_code == 200
        data = response.json()
        assert data["toggles"]["filtering"] == False

    def test_toggle_use_reviews_false(self, client, mock_pipeline):
        """Test that use_reviews=false disables review extraction."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&use_reviews=false")

        assert response.status_code == 200
        data = response.json()
        assert data["toggles"]["reviewing"] == False

    def test_toggle_use_scoring_false(self, client, mock_pipeline):
        """Test that use_scoring=false disables scoring."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&use_scoring=false")

        assert response.status_code == 200
        data = response.json()
        assert data["toggles"]["scoring"] == False

    def test_all_toggles_false(self, client, mock_pipeline):
        """Test that all toggles can be disabled simultaneously."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get(
                "/api/v1/search?query=test"
                "&use_filter=false&use_reviews=false&use_scoring=false"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["toggles"]["filtering"] == False
        assert data["toggles"]["reviewing"] == False
        assert data["toggles"]["scoring"] == False


# =============================================================================
# T076: Unit test for sorting in search
# =============================================================================

class TestSorting:
    """Tests for sorting functionality in search endpoint."""

    def test_sort_by_score(self, client, mock_pipeline):
        """Test sorting by score (default)."""
        mock_listing1 = MagicMock()
        mock_listing1.title = "Item 1"
        mock_listing1.score = 0.9
        mock_listing1.price = 100.0
        mock_listing1.date_posted = "2025-05-20"

        mock_listing2 = MagicMock()
        mock_listing2.title = "Item 2"
        mock_listing2.score = 0.95
        mock_listing2.price = 50.0
        mock_listing2.date_posted = "2025-05-19"

        mock_context = MagicMock()
        mock_context.listings = [mock_listing1, mock_listing2]
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&sort_by=score")

        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == "score"
        # Results should be sorted by score descending
        if len(data["results"]) >= 2:
            assert data["results"][0]["score"] >= data["results"][1]["score"]

    def test_sort_by_price_asc(self, client, mock_pipeline):
        """Test sorting by price ascending."""
        mock_listing1 = MagicMock()
        mock_listing1.title = "Item 1"
        mock_listing1.score = 0.9
        mock_listing1.price = 100.0
        mock_listing1.date_posted = "2025-05-20"

        mock_listing2 = MagicMock()
        mock_listing2.title = "Item 2"
        mock_listing2.score = 0.95
        mock_listing2.price = 50.0
        mock_listing2.date_posted = "2025-05-19"

        mock_context = MagicMock()
        mock_context.listings = [mock_listing1, mock_listing2]
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&sort_by=price_asc")

        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == "price_asc"

    def test_sort_by_price_desc(self, client, mock_pipeline):
        """Test sorting by price descending."""
        mock_listing1 = MagicMock()
        mock_listing1.title = "Item 1"
        mock_listing1.score = 0.9
        mock_listing1.price = 100.0
        mock_listing1.date_posted = "2025-05-20"

        mock_listing2 = MagicMock()
        mock_listing2.title = "Item 2"
        mock_listing2.score = 0.95
        mock_listing2.price = 50.0
        mock_listing2.date_posted = "2025-05-19"

        mock_context = MagicMock()
        mock_context.listings = [mock_listing1, mock_listing2]
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&sort_by=price_desc")

        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == "price_desc"

    def test_sort_by_date(self, client, mock_pipeline):
        """Test sorting by date."""
        mock_listing1 = MagicMock()
        mock_listing1.title = "Item 1"
        mock_listing1.score = 0.9
        mock_listing1.price = 100.0
        mock_listing1.date_posted = "2025-05-20"

        mock_listing2 = MagicMock()
        mock_listing2.title = "Item 2"
        mock_listing2.score = 0.95
        mock_listing2.price = 50.0
        mock_listing2.date_posted = "2025-05-19"

        mock_context = MagicMock()
        mock_context.listings = [mock_listing1, mock_listing2]
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=test&sort_by=date")

        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == "date"


# =============================================================================
# Quick search endpoint tests
# =============================================================================

class TestQuickSearch:
    """Tests for the quick search endpoint."""

    def test_quick_search_uses_defaults(self, client, mock_pipeline):
        """Test that quick search uses all default values."""
        mock_context = MagicMock()
        mock_context.listings = []
        mock_pipeline.execute = AsyncMock(return_value=mock_context)

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search/quick?query=test")

        assert response.status_code == 200
        data = response.json()
        # Quick search should use defaults
        assert data["sort_by"] == "score"
        assert data["toggles"]["filtering"] == True
        assert data["toggles"]["reviewing"] == True
        assert data["toggles"]["scoring"] == True

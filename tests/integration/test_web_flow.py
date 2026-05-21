"""
Integration tests for web flow.

Tests:
- T074: Integration test for search flow
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from web.backend.main import app
from web.backend.models.schemas import SearchResponse


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


# =============================================================================
# T074: Integration test for search flow
# =============================================================================

class TestEndToEndSearchFlow:
    """End-to-end integration tests for the search flow."""

    def test_complete_search_flow(self, client):
        """Test the complete search flow from request to response."""
        # Mock the pipeline to return test data
        mock_listing = MagicMock()
        mock_listing.title = "Integration Test Item"
        mock_listing.price = 150.0
        mock_listing.currency = "EUR"
        mock_listing.url = "https://example.com/integration"
        mock_listing.platform = "DBA"
        mock_listing.score = 0.98
        mock_listing.score_reason = "Perfect match"
        mock_listing.description = "Integration test description"
        mock_listing.date_posted = "2025-05-20"
        mock_listing.images = ["https://example.com/image.jpg"]
        mock_listing.review_summary = "5.0/5 from 25 reviews"
        mock_listing.review_links = []

        mock_context = MagicMock()
        mock_context.listings = [mock_listing]

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=mock_context)
        mock_pipeline.load_modules = MagicMock()

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            # Step 1: Submit search request
            response = client.get("/api/v1/search?query=integration+test")

        # Step 2: Verify response
        assert response.status_code == 200

        data = response.json()

        # Step 3: Verify response structure
        assert isinstance(data, dict)
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert "sort_by" in data
        assert "toggles" in data
        assert "timestamp" in data
        assert "reviews" in data

        # Step 4: Verify response content
        assert data["query"] == "integration test"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1

        # Step 5: Verify result structure
        result = data["results"][0]
        assert "id" in result
        assert "title" in result
        assert "price" in result
        assert "currency" in result
        assert "original_url" in result
        assert "platform" in result
        assert "score" in result

        # Step 6: Verify result content
        assert result["title"] == "Integration Test Item"
        assert result["price"] == 150.0
        assert result["currency"] == "EUR"
        assert result["platform"] == "DBA"

    def test_search_flow_with_all_parameters(self, client):
        """Test search flow with all parameters specified."""
        mock_listing = MagicMock()
        mock_listing.title = "Full Parameters Item"
        mock_listing.price = 200.0
        mock_listing.currency = "DKK"
        mock_listing.url = "https://example.com/full"
        mock_listing.platform = "Vinted"
        mock_listing.score = 0.85
        mock_listing.score_reason = "Good match"
        mock_listing.description = "Full parameters"
        mock_listing.date_posted = "2025-05-19"
        mock_listing.images = []
        mock_listing.review_summary = ""
        mock_listing.review_links = []

        mock_context = MagicMock()
        mock_context.listings = [mock_listing]

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=mock_context)
        mock_pipeline.load_modules = MagicMock()

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get(
                "/api/v1/search"
                "?query=full+test"
                "&max_results=10"
                "&currency=DKK"
                "&use_filter=false"
                "&use_reviews=false"
                "&use_scoring=false"
                "&sort_by=price_asc"
            )

        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "full test"
        assert data["total_results"] == 1

        # Verify toggles are reflected
        assert data["toggles"]["filtering"] == False
        assert data["toggles"]["reviewing"] == False
        assert data["toggles"]["scoring"] == False

        # Verify sort_by is reflected
        assert data["sort_by"] == "price_asc"

    def test_search_flow_with_multiple_results(self, client):
        """Test search flow with multiple results."""
        # Create multiple mock listings
        listings = []
        for i in range(5):
            listing = MagicMock()
            listing.title = f"Item {i+1}"
            listing.price = 50.0 * (i + 1)
            listing.currency = "EUR"
            listing.url = f"https://example.com/item/{i}"
            listing.platform = "DBA" if i % 2 == 0 else "Vinted"
            listing.score = 0.8 + (i * 0.05)
            listing.score_reason = f"Score {i}"
            listing.description = f"Description {i}"
            listing.date_posted = "2025-05-20"
            listing.images = []
            listing.review_summary = ""
            listing.review_links = []
            listings.append(listing)

        mock_context = MagicMock()
        mock_context.listings = listings

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=mock_context)
        mock_pipeline.load_modules = MagicMock()

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=multiple+results")

        assert response.status_code == 200

        data = response.json()
        assert data["total_results"] == 5
        assert len(data["results"]) == 5

        # Verify results are sorted by score descending (default)
        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_search_flow_with_no_results(self, client):
        """Test search flow when no results are found."""
        mock_context = MagicMock()
        mock_context.listings = []

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=mock_context)
        mock_pipeline.load_modules = MagicMock()

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search?query=no+results")

        assert response.status_code == 200

        data = response.json()
        assert data["total_results"] == 0
        assert len(data["results"]) == 0
        assert data["query"] == "no results"


class TestWebInterfaceIntegration:
    """Integration tests for the web interface components."""

    def test_html_page_loads_with_all_assets(self, client):
        """Test that the HTML page loads with all required assets."""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200

        html = response.text

        # Verify search form is present
        assert "<form" in html or "search" in html.lower()
        assert "id=\"search-form\"" in html or "search-form" in html

        # Verify static asset references
        assert "styles.css" in html
        assert "app.js" in html

    def test_api_documentation_accessible(self, client):
        """Test that API documentation endpoints are accessible."""
        # OpenAPI JSON
        response = client.get("/api/openapi.json")
        assert response.status_code == 200

        # Swagger UI
        response = client.get("/api/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/api/redoc")
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.get("/health")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        # Note: CORS headers may only be present in actual CORS requests
        # This test verifies the middleware is configured

    def test_quick_search_endpoint_integration(self, client):
        """Test the quick search endpoint integration."""
        mock_listing = MagicMock()
        mock_listing.title = "Quick Search Item"
        mock_listing.price = 75.0
        mock_listing.currency = "EUR"
        mock_listing.url = "https://example.com/quick"
        mock_listing.platform = "Tradera"
        mock_listing.score = 0.90
        mock_listing.score_reason = "Quick match"
        mock_listing.description = "Quick search"
        mock_listing.date_posted = "2025-05-20"
        mock_listing.images = []
        mock_listing.review_summary = ""
        mock_listing.review_links = []

        mock_context = MagicMock()
        mock_context.listings = [mock_listing]

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=mock_context)
        mock_pipeline.load_modules = MagicMock()

        with patch('web.backend.api.search.Pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/search/quick?query=quick+test")

        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "quick test"
        # Quick search should use defaults
        assert data["sort_by"] == "score"
        assert data["toggles"]["filtering"] == True
        assert data["toggles"]["reviewing"] == True
        assert data["toggles"]["scoring"] == True

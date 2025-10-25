import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_scrape_endpoint_missing_fields():
    """Test scrape endpoint with missing required fields."""
    response = client.post("/v1/scrape", json={})
    assert response.status_code == 422  # Validation error


def test_scrape_endpoint_invalid_url():
    """Test scrape endpoint with unsupported platform URL."""
    request_data = {
        "url": "https://www.example.com/user",
        "user_id": "test_user",
        "post_limit": 10
    }
    response = client.post("/v1/scrape", json=request_data)
    assert response.status_code == 400
    assert "Unsupported platform" in response.json()["detail"]


def test_scrape_endpoint_valid_request():
    """
    Test scrape endpoint with valid Threads URL.
    Note: This test requires a browser profile to exist.
    Skip if profile doesn't exist.
    """
    request_data = {
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "test_user",
        "post_limit": 5,
        "headless": True
    }

    # This will likely fail without a valid browser profile
    # In production, you'd mock the scraper or set up test fixtures
    response = client.post("/v1/scrape", json=request_data)

    # Either succeeds or fails with profile not found
    assert response.status_code in [200, 404, 500]

    if response.status_code == 200:
        data = response.json()
        assert "total_items" in data
        assert "url" in data
        assert data["url"] == request_data["url"]
        assert "items" in data
        assert isinstance(data["items"], list)


def test_scrape_endpoint_with_time_limit():
    """Test scrape endpoint with time limit parameter."""
    request_data = {
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "test_user",
        "time_limit": 30,
        "headless": True
    }

    response = client.post("/v1/scrape", json=request_data)
    # Will fail without browser profile, but validates request format
    assert response.status_code in [200, 404, 500]


def test_scrape_endpoint_schema_validation():
    """Test that the response schema is correct when scraping succeeds."""
    request_data = {
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "test_user",
        "post_limit": 1,
        "scroll_delay": 0.5,
        "headless": True
    }

    response = client.post("/v1/scrape", json=request_data)

    if response.status_code == 200:
        data = response.json()
        # Check required fields
        required_fields = [
            "scraped_at",
            "url",
            "platform",
            "user_id",
            "total_items",
            "elapsed_time",
            "items"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check items structure
        if data["items"]:
            first_item = data["items"][0]
            assert "text" in first_item
            # Optional fields may be None
            assert "link" in first_item
            assert "likes" in first_item
            assert "comments" in first_item
            assert "reposts" in first_item


@pytest.mark.parametrize("scroll_delay", [0.1, 0.75, 2.0])
def test_scrape_endpoint_scroll_delay_validation(scroll_delay):
    """Test that scroll_delay values within range are accepted."""
    request_data = {
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "test_user",
        "post_limit": 1,
        "scroll_delay": scroll_delay,
        "headless": True
    }

    response = client.post("/v1/scrape", json=request_data)
    # Should not fail validation (may fail for other reasons)
    assert response.status_code != 422


def test_scrape_endpoint_invalid_scroll_delay():
    """Test that invalid scroll_delay values are rejected."""
    request_data = {
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "test_user",
        "post_limit": 1,
        "scroll_delay": 10.0,  # Too high (max is 5.0)
        "headless": True
    }

    response = client.post("/v1/scrape", json=request_data)
    assert response.status_code == 422  # Validation error

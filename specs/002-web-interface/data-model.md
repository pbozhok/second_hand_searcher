# Data Model: Web Interface for Search Tool

**Feature**: 002-web-interface  
**Date**: 2025-05-21  
**Spec**: [specs/002-web-interface/spec.md](./spec.md)  
**Plan**: [specs/002-web-interface/plan.md](./plan.md)

## Overview

This document defines the data structures and entities for the web interface feature. It maps between:
1. **Web API Models** (Pydantic models used by FastAPI)
2. **Frontend Models** (JSON structures sent to browser)
3. **Core Models** (existing models from `models.py`)

## Entity Relationships

```
┌─────────────────┐
│    User         │
│  (implied)      │
└────────┬────────┘
         │
         │ submits
         ▼
┌─────────────────┐
│  SearchRequest  │
│  (API Input)    │
└────────┬────────┘
         │
         │ processed by
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Pipeline       │◄────│   PipelineConfig│
│  (existing core) │     │  (existing core) │
└────────┬────────┘     └─────────────────┘
         │
         │ produces
         ▼
┌─────────────────┐    ┌─────────────────┐
│  SearchResult   │    │      Review     │
│  (API Output)   │    │  (API Output)    │
└────────┬────────┘    └────────┬────────┘
         │                        │
         │ contains               │ related to
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│    ItemCard     │◄─────│   ReviewInfo    │
│  (Frontend)      │      │  (Frontend)      │
└─────────────────┘      └─────────────────┘
```

---

## API Models (Pydantic)

### SearchRequest

**Purpose**: Input model for search endpoint

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| query | str | Yes | - | Search query string |
| max_results | int | No | 40 | Maximum number of results to return |
| currency | str | No | "EUR" | Target currency for price conversion |
| use_filter | bool | No | true | Enable LLM-based filtering |
| use_reviews | bool | No | true | Enable review extraction |
| use_scoring | bool | No | true | Enable LLM-based scoring |
| sort_by | str | No | "score" | Sort results by: score, price_asc, price_desc, date |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    max_results: Optional[int] = Field(default=40, ge=1, le=100, description="Maximum results")
    currency: Optional[str] = Field(default="EUR", description="Target currency")
    use_filter: Optional[bool] = Field(default=True, description="Enable filtering")
    use_reviews: Optional[bool] = Field(default=True, description="Enable reviews")
    use_scoring: Optional[bool] = Field(default=True, description="Enable scoring")
    sort_by: Optional[str] = Field(default="score", description="Sort order")
```

---

### ItemResponse

**Purpose**: Individual item in search results

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | str | Yes | Unique identifier for the item |
| title | str | Yes | Item title |
| price | float | No | Item price |
| currency | str | No | Currency code (EUR, DKK, SEK) |
| posted_date | str | No | Date posted (ISO format YYYY-MM-DD) |
| original_url | str | Yes | URL to original advertisement |
| image_url | str | No | URL to item image |
| platform | str | Yes | Source platform (DBA, Vinted, Tradera) |
| score | float | No | Relevance score (0.0 to 1.0) |
| description | str | No | Item description (truncated) |
| location | str | No | Item location |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ItemResponse(BaseModel):
    id: str = Field(..., description="Unique item identifier")
    title: str = Field(..., description="Item title")
    price: Optional[float] = Field(default=None, description="Item price")
    currency: Optional[str] = Field(default=None, description="Currency code")
    posted_date: Optional[str] = Field(default=None, description="Date posted (YYYY-MM-DD)")
    original_url: str = Field(..., description="URL to original advertisement")
    image_url: Optional[str] = Field(default=None, description="URL to item image")
    platform: str = Field(..., description="Source platform")
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Relevance score")
    description: Optional[str] = Field(default=None, max_length=500, description="Item description")
    location: Optional[str] = Field(default=None, description="Item location")
```

---

### ReviewResponse

**Purpose**: Review information for an item

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| item_id | str | Yes | Reference to item |
| average_rating | float | No | Average rating (1.0 to 5.0) |
| review_count | int | No | Number of reviews |
| summary | str | No | Summarized review text |
| sentiment | str | No | Overall sentiment (positive, neutral, negative) |
| source | str | No | Review source |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class ReviewResponse(BaseModel):
    item_id: str = Field(..., description="Reference to item")
    average_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="Average rating")
    review_count: Optional[int] = Field(default=None, ge=0, description="Number of reviews")
    summary: Optional[str] = Field(default=None, max_length=1000, description="Summarized review text")
    sentiment: Optional[str] = Field(default=None, description="Overall sentiment")
    source: Optional[str] = Field(default=None, description="Review source")
```

---

### SearchResponse

**Purpose**: Complete response for search endpoint

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | str | Yes | Original search query |
| results | list[ItemResponse] | Yes | List of matching items |
| total_results | int | Yes | Total number of results |
| sort_by | str | Yes | Current sort order |
| toggles | dict | Yes | Current toggle states |
| timestamp | str | Yes | Response timestamp |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ToggleStates(BaseModel):
    filtering: bool = Field(default=True, description="Filtering enabled")
    reviewing: bool = Field(default=True, description="Reviewing enabled")
    scoring: bool = Field(default=True, description="Scoring enabled")

class SearchResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    results: List[ItemResponse] = Field(default_factory=list, description="List of matching items")
    total_results: int = Field(default=0, description="Total number of results")
    sort_by: str = Field(default="score", description="Current sort order")
    toggles: ToggleStates = Field(default_factory=ToggleStates, description="Current toggle states")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")
```

---

### ErrorResponse

**Purpose**: Standard error response format

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| error | str | Yes | Error type |
| message | str | Yes | Human-readable error message |
| details | dict | No | Additional error details |

**Pydantic Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
```

---

## Frontend Models (JSON)

### ItemCard

**Purpose**: Item data for frontend card display

**Structure**:
```json
{
  "id": "dba-12345",
  "title": "Vintage Leather Jacket",
  "price": 99.99,
  "currency": "EUR",
  "formatted_price": "€99.99",
  "posted_date": "2025-05-20",
  "formatted_date": "May 20, 2025",
  "original_url": "https://dba.dk/item/12345",
  "image_url": "https://dba.dk/images/12345.jpg",
  "platform": "DBA",
  "score": 0.95,
  "location": "Copenhagen",
  "review": {
    "average_rating": 4.5,
    "review_count": 12,
    "summary": "Great condition, fast shipping"
  }
}
```

**Derivation**: From `ItemResponse` + `ReviewResponse` with formatted fields for display

---

### FrontendState

**Purpose**: Complete frontend state

**Structure**:
```json
{
  "query": "",
  "results": [],
  "total_results": 0,
  "is_searching": false,
  "error": null,
  "sort_by": "score",
  "toggles": {
    "filtering": true,
    "reviewing": true,
    "scoring": true
  },
  "search_bar_position": "center"
}
```

---

## Core Model Mapping

### From Core Listing to API ItemResponse

The existing `models.py` contains a `Listing` class. Mapping:

| Core Listing Field | API ItemResponse Field | Transformation |
|--------------------|------------------------|---------------|
| id | id | Direct |
| title | title | Direct |
| price | price | Direct |
| currency | currency | Direct |
| date | posted_date | Format as YYYY-MM-DD |
| url | original_url | Direct |
| image_url | image_url | Direct |
| platform | platform | Direct |
| score | score | Direct |
| description | description | Truncate to 500 chars |
| location | location | Direct |

---

### Adapter Functions

**Location**: `web/shared/adapters.py`

**Functions**:

```python
# Convert core Listing to API ItemResponse
def listing_to_item_response(listing: Listing) -> ItemResponse:
    return ItemResponse(
        id=str(listing.id),
        title=listing.title,
        price=listing.price,
        currency=listing.currency,
        posted_date=listing.date.strftime("%Y-%m-%d") if listing.date else None,
        original_url=listing.url,
        image_url=listing.image_url,
        platform=listing.platform,
        score=listing.score,
        description=listing.description[:500] if listing.description else None,
        location=listing.location
    )

# Convert API ItemResponse to Frontend ItemCard
def item_response_to_item_card(item: ItemResponse, review: Optional[ReviewResponse] = None) -> dict:
    # Format price based on currency
    currency_symbols = {"EUR": "€", "DKK": "kr", "SEK": "kr"}
    symbol = currency_symbols.get(item.currency, "")
    formatted_price = f"{symbol}{item.price:.2f}" if item.price else None
    
    # Format date
    formatted_date = item.posted_date  # Already YYYY-MM-DD from API
    
    return {
        **item.dict(),
        "formatted_price": formatted_price,
        "formatted_date": formatted_date,
        "review": review.dict() if review else None
    }
```

---

## Validation Rules

### SearchRequest Validation

1. **query**: Must be 1-500 characters, non-empty after trimming
2. **max_results**: Must be between 1 and 100
3. **currency**: Must be one of: EUR, DKK, SEK
4. **sort_by**: Must be one of: score, price_asc, price_desc, date

### ItemResponse Validation

1. **id**: Must be unique within results
2. **title**: Must be 1-200 characters
3. **price**: Must be >= 0 if present
4. **score**: Must be between 0.0 and 1.0 if present
5. **original_url**: Must be valid URL format
6. **image_url**: Must be valid URL format or null

---

## State Transitions

### Search Flow

```
┌─────────┐    query submitted    ┌──────────┐
│  Idle   │ ─────────────────────►│ Searching │
└─────────┘                        └──────────┘
                                     │
                                     │ results ready
                                     ▼
┌─────────┐    new query     ┌───────────┐
│  Idle   │ ◄─────────────────│ Results   │
└─────────┘    or clear        └───────────┘
```

### Sort Flow

```
┌───────────┐    sort changed    ┌───────────┐
│  Results  │ ───────────────────►│ Re-sorting │
└───────────┘                     └───────────┘
                                      │
                                      │ sorted
                                      ▼
                                 ┌───────────┐
                                 │  Results  │
                                 └───────────┘
```

### Toggle Flow

```
┌───────────┐    toggle changed    ┌─────────────┐
│  Results  │ ────────────────────►│ Re-searching │
└───────────┘                      └─────────────┘
                                       │
                                       │ results ready
                                       ▼
                                  ┌───────────┐
                                  │  Results  │
                                  └───────────┘
```

---

## Data Flow

```
User
  │
  ▼
┌─────────────┐
│   Browser    │
└──────┬──────┘
       │ HTTP Request (SearchRequest)
       ▼
┌─────────────┐
│  FastAPI     │
│  Endpoint    │
└──────┬──────┘
       │ Adapt (SearchRequest → Pipeline input)
       ▼
┌─────────────┐
│   Adapter   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Pipeline   │◄─────────────┐
│  (existing)  │               │
└──────┬──────┘               │
       │                      │
       ▼                      │
┌─────────────┐               │
│  Adapters    │◄──────────────┘
│  (ItemResponse)
└──────┬──────┘
       │ HTTP Response (SearchResponse)
       ▼
┌─────────────┐
│   Browser    │
└──────┬──────┘
       │
       ▼
   Render Cards
```

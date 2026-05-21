# Quickstart: Web Interface for Search Tool

**Feature**: 002-web-interface  
**Date**: 2025-05-21  
**Spec**: [specs/002-web-interface/spec.md](./spec.md)  
**Plan**: [specs/002-web-interface/plan.md](./plan.md)

## Overview

This guide helps you get the web interface running quickly for development and testing purposes.

## Prerequisites

### Existing Dependencies (already installed)
- Python 3.11+
- httpx
- BeautifulSoup4
- rich

### New Dependencies (to be installed)
```bash
# Backend
pip install fastapi uvicorn python-multipart

# Frontend (for development)
# No build step required - just static files

# Testing
pip install pytest playwright httpx
playwright install
```

---

## Installation

### 1. Install the web module

```bash
cd /path/to/second_hand_searcher

# Install new dependencies
pip install -r requirements-web.txt  # (create this file)
```

### 2. Environment Setup

Create `.env.web` file (optional - for web-specific settings):
```bash
# Web server settings
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_DEBUG=true

# Shared with CLI
GEMINI_API_KEY=your_api_key  # or MISTRAL_API_KEY
SERPAPI_KEY=your_serpapi_key  # optional
```

---

## Running the Web Interface

### Development Mode

```bash
# Start the FastAPI server
cd /path/to/second_hand_searcher
uvicorn web.backend.main:app --reload --port 8000

# Or with environment file
uvicorn web.backend.main:app --reload --port 8000 --env-file .env.web
```

Then open your browser to: http://localhost:8000

### Production Mode

```bash
# Without reload, multiple workers
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Gunicorn for production
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 web.backend.main:app
```

---

## Running Tests

### Backend Tests

```bash
# Run all web backend tests
pytest web/backend/tests/ -v

# Run specific test file
pytest web/backend/tests/test_search.py -v

# Run with coverage
pytest web/backend/tests/ --cov=web.backend --cov-report=html
```

### Frontend Tests

```bash
# Run Playwright tests
pytest tests/frontend/ -v

# Run specific frontend test
pytest tests/frontend/test_search.py -v

# Run with headed browser (for debugging)
pytest tests/frontend/ -v --headed
```

---

## Project Structure

```text
second_hand_searcher/
├── web/                      # NEW: Web interface
│   ├── backend/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── search.py     # Search endpoints
│   │   │   └── items.py      # Item data endpoints
│   │   ├── models/
│   │   │   └── schemas.py    # Pydantic models
│   │   ├── shared/
│   │   │   └── adapters.py   # Core ↔ API adapters
│   │   └── tests/
│   │       ├── test_search.py
│   │       ├── test_items.py
│   │       └── test_adapters.py
│   │
│   └── frontend/
│       ├── static/
│       │   ├── css/
│       │   │   └── styles.css
│       │   └── js/
│       │       └── app.js
│       └── templates/
│           └── index.html
│
├── core/                     # EXISTING: Core modules (unchanged)
│   ├── pipeline.py
│   ├── registry.py
│   └── injection.py
│
├── scrapers/                 # EXISTING: Scrapers (unchanged)
├── processors/               # EXISTING: Processors (unchanged)
├── filters/                  # EXISTING: Filters (unchanged)
├── rankers/                  # EXISTING: Rankers (unchanged)
├── reviewers/                # EXISTING: Reviewers (unchanged)
│
├── second_hand_research.py   # EXISTING: CLI entry (unchanged)
├── config.py                 # EXISTING: Config (extended)
└── models.py                 # EXISTING: Models (unchanged)
```

---

## Configuration

### Main Configuration File

The existing `config.py` will be extended with web-specific settings:

```python
# Web-specific configuration
class WebConfig:
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False
    
    # CORS settings
    CORS_ORIGINS = ["*"]  # For development only
    
    # Static files
    STATIC_DIR = "web/frontend/static"
    TEMPLATES_DIR = "web/frontend/templates"
    
    # API settings
    API_PREFIX = "/api/v1"
    MAX_CONCURRENT_SEARCHES = 10
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| WEB_HOST | No | 0.0.0.0 | Web server host |
| WEB_PORT | No | 8000 | Web server port |
| WEB_DEBUG | No | false | Enable debug mode |
| GEMINI_API_KEY | Yes | - | Google Gemini API key |
| MISTRAL_API_KEY | No | - | Mistral API key (alternative) |
| SERPAPI_KEY | No | - | SerpAPI key for reviews |

---

## API Endpoints

### Search

```
GET /api/v1/search?query={query}&max_results=40&currency=EUR&sort_by=score
```

**Parameters**:
- `query` (required): Search query string
- `max_results` (optional): Max results (1-100, default: 40)
- `currency` (optional): EUR, DKK, or SEK (default: EUR)
- `use_filter` (optional): Enable filtering (default: true)
- `use_reviews` (optional): Enable reviews (default: true)
- `use_scoring` (optional): Enable scoring (default: true)
- `sort_by` (optional): score, price_asc, price_desc, date (default: score)

**Example**:
```bash
curl "http://localhost:8000/api/v1/search?query=leather+jacket&max_results=20"
```

**Response**: See [contracts/api/search.yaml](./contracts/api/search.yaml)

### Quick Search

```
GET /api/v1/search/quick?query={query}
```

Simplified endpoint with all defaults.

---

## Frontend Development

### File Locations

- **HTML templates**: `web/frontend/templates/`
- **CSS**: `web/frontend/static/css/`
- **JavaScript**: `web/frontend/static/js/`

### Key Files

#### index.html
Main HTML template with:
- Search bar (centered initially)
- Results container
- Loading indicator
- Error message display

#### styles.css
Contains:
- Search bar styling and animation
- Card grid layout
- Card hover effects
- Responsive breakpoints
- Loading animations

#### app.js
Contains:
- htmx initialization
- Search form handling
- Card rendering logic
- Sort and toggle state management
- Error handling

### Development Workflow

1. Edit files in `web/frontend/`
2. Server automatically reloads (with `--reload` flag)
3. Refresh browser to see changes
4. No build step required

---

## CLI Compatibility

The existing CLI continues to work unchanged:

```bash
# CLI still works as before
python second_hand_research.py "leather jacket" --debug

# Web and CLI can run simultaneously
# Terminal 1: uvicorn web.backend.main:app --reload
# Terminal 2: python second_hand_research.py "query"
```

---

## Troubleshooting

### Common Issues

**Server won't start**:
```bash
# Check port is available
lsof -i :8000

# Try different port
uvicorn web.backend.main:app --port 8001
```

**Dependencies missing**:
```bash
pip install fastapi uvicorn
```

**CORS errors in development**:
```python
# In web/backend/main.py, add:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**API returns 500 error**:
```bash
# Check server logs
# Enable debug mode
uvicorn web.backend.main:app --reload --log-level debug
```

---

## Docker (Optional)

For containerized deployment:

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Run**:
```bash
docker build -t secondhand-search .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key secondhand-search
```

---

## Next Steps

After getting the web interface running:

1. **Test the search flow**: Try different queries and verify results
2. **Test toggles**: Turn filtering and reviewing on/off
3. **Test sorting**: Change sort order and verify results reorder
4. **Test responsive**: Resize browser and verify layout adapts
5. **Test mobile**: Open on mobile device and verify touch targets

For development:
- See [plan.md](./plan.md) for implementation details
- See [data-model.md](./data-model.md) for data structures
- See [contracts/api/](./contracts/api/) for API specifications

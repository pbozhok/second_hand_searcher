# Implementation Plan: Web Interface for Search Tool

**Branch**: `002-web-interface` | **Date**: 2025-05-21 | **Spec**: [specs/002-web-interface/spec.md](../spec.md)

**Input**: Feature specification from `/specs/002-web-interface/spec.md`

## Summary

Add a modern, dynamic web interface to the existing CLI-based second-hand search tool. The web interface will provide browser-based access to search functionality with visual card-based results, while maintaining 100% compatibility with existing CLI operations. The implementation will leverage the existing modular architecture (scrapers, filters, processors, rankers) and add a new web layer.

## Technical Context

**Language/Version**: Python 3.11 (matching existing codebase)

**Primary Dependencies**: 
- Backend: FastAPI (for REST API), uvloop (for async performance)
- Frontend: React (via htmx for simplicity and minimal JS) or pure HTML/CSS/JS for static serving
- Shared: httpx, BeautifulSoup (existing), rich (existing)

**Storage**: N/A (web interface uses existing in-memory data flow from scrapers)

**Testing**: pytest (existing) + Playwright for frontend integration tests

**Target Platform**: Web browsers (desktop and mobile responsive)

**Project Type**: web-service (frontend + backend API)

**Performance Goals**: 
- Page load time < 2 seconds
- Search response time < 3 seconds
- Card rendering < 500ms for 20 items

**Constraints**: 
- Must not modify existing CLI functionality
- Must reuse existing module architecture (scrapers, filters, processors, rankers)
- Must support concurrent searches from multiple users
- Must handle missing data gracefully (images, prices, dates)

**Scale/Scope**: 
- Single-page application with dynamic search
- Supports 10+ concurrent users (initial scope)
- Displays 20-40 item cards per search
- 5-10 MB memory per active search session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: CLI-First

**Status**: ✅ PASS

**Analysis**: The web interface is an **additive** feature that does not modify the CLI. All CLI functionality remains intact via `second_hand_research.py`. The web interface will call the same core modules (Pipeline, scrapers, filters) through a new API layer.

**Justification**: 
- Existing CLI entry point (`second_hand_research.py`) is untouched
- New web layer will be in separate directory (`web/` or `frontend/` + `backend/`)
- Core modules (`core/pipeline.py`, scrapers, filters, processors, rankers) remain shared
- CLI commands continue to work via text in/out protocol

### Principle II: Modular Design

**Status**: ✅ PASS

**Analysis**: The existing architecture is already modular with independent scrapers, filters, processors, and rankers. The web interface will:
1. Add a new **API module** (FastAPI) that orchestrates existing modules
2. Add a new **frontend module** (static files) that consumes the API
3. Not modify any existing module interfaces

**Justification**: 
- New API layer uses Dependency Injection to inject existing services
- Each web endpoint maps to existing pipeline stages
- Frontend is decoupled from backend via REST API
- All existing modules can be bypassed or swapped as before

### Principle III: Test-First

**Status**: ✅ PASS

**Analysis**: Test plan documented in research.md. All new features will have corresponding tests written before implementation.

**Test Coverage Plan**:
- **Unit tests** (pytest): API endpoints, adapters, error handling
- **Integration tests** (pytest): End-to-end search flow
- **Frontend tests** (Playwright): Page rendering, user interactions, responsive behavior
- **Contract tests**: API endpoint validation against contracts

**Test Files**:
```text
web/backend/tests/
├── test_search.py      # Search endpoint tests
├── test_items.py       # Item data endpoint tests
├── test_adapters.py    # Adapter layer tests
└── test_errors.py      # Error handling tests

tests/integration/
└── test_web_flow.py   # End-to-end web flow tests

tests/frontend/
├── test_homepage.py    # Homepage rendering and interactions
├── test_search.py      # Search functionality tests
├── test_cards.py       # Card display and hover tests
└── test_responsive.py  # Responsive design tests
```

**Test Requirements**:
- All API endpoints must have unit tests
- All user scenarios from spec must have integration tests
- Frontend must have Playwright tests for critical paths
- Tests must pass before merging

**Justification**: 
- Test plan explicitly documented in research.md
- Test files structure defined above
- All critical paths covered by automated tests
- Follows existing project pattern (pytest for backend)

## Project Structure

### Documentation (this feature)

```text
specs/002-web-interface/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── api/             # API endpoint contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
# Core modules (existing, unchanged)
core/
├── logging.py
├── pipeline.py
├── registry.py
└── injection.py

scrapers/
processors/
filters/
rankers/
reviewers/

# New web modules
web/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── search.py     # Search endpoints
│   │   └── items.py      # Item data endpoints
│   ├── models/
│   │   └── schemas.py    # Pydantic models for API
│   └── tests/
│       ├── test_search.py
│       └── test_items.py
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       └── index.html
│
└── shared/
    └── adapters.py       # Adapters between web models and core models

# CLI entry point (unchanged)
second_hand_research.py

# Configuration (extended)
config.py                # Add web-specific config
```

**Structure Decision**: Option 2 (Web application) selected because the feature requires both frontend and backend components. The `web/` directory contains all new code, keeping existing code untouched. Backend API uses FastAPI for async support matching the existing async scraper architecture.

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design completion*

### Principle I: CLI-First

**Status**: ✅ PASS (confirmed)

**Verification**: Design explicitly keeps CLI entry point (`second_hand_research.py`) unchanged. Web interface is additive only.

### Principle II: Modular Design

**Status**: ✅ PASS (confirmed)

**Verification**: 
- New `web/` directory is completely separate from existing code
- Uses Adapter Pattern to connect to existing modules
- Existing modules (scrapers, filters, processors, rankers) remain untouched
- All new modules follow single responsibility principle

### Principle III: Test-First

**Status**: ✅ PASS (confirmed)

**Verification**: 
- Test structure documented in plan
- Test files identified for all new components
- Testing approach defined for both backend (pytest) and frontend (Playwright)

**Overall Gate**: ✅ ALL PRINCIPLES PASS - Ready for Phase 2

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New FastAPI dependency | Required for web API layer | Flask would work but FastAPI provides better async support matching existing httpx-based scrapers |
| New htmx dependency | Required for dynamic frontend | Server-side rendering alone cannot provide the dynamic card hover and sorting features |


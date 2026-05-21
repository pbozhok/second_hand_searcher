# Research: Web Interface for Search Tool

**Feature**: 002-web-interface  
**Date**: 2025-05-21  
**Status**: Complete  
**Spec**: [specs/002-web-interface/spec.md](./spec.md)

## Decisions

### Decision 1: Frontend Technology Stack

**Context**: The web interface requires dynamic behavior including:
- Search bar that moves on validation
- Card hover effects showing reviews
- Dynamic sorting of results
- Toggle controls for filtering and reviewing

**Decision**: Use **htmx + Hyperscript** with vanilla CSS

**Rationale**: 
- Minimal JavaScript footprint (<10KB combined)
- Progressive enhancement - works without JS (basic search)
- Full dynamic behavior with JS enabled
- No build step required (just static files)
- Matches the existing project's philosophy of simplicity
- Easy to maintain and debug

**Alternatives Considered**:
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Vanilla JS | No dependencies, full control | More code to write, harder to maintain | Rejected - too much boilerplate |
| React | Rich ecosystem, component-based | Requires build step, heavier, more complex | Rejected - overkill for this scope |
| Vue | Lighter than React, simpler | Still requires build step | Rejected - unnecessary complexity |
| htmx | Minimal JS, progressive enhancement | Less known, limited for complex state | **Selected** |
| Alpine.js | Lightweight, declarative | Another dependency | Rejected - htmx is simpler |

**Implementation**: 
- htmx for AJAX requests and DOM updates
- Hyperscript for client-side state (toggles, sorting)
- Vanilla CSS for styling and animations
- FastAPI serves static files

---

### Decision 2: Backend Framework

**Context**: Need a web framework that:
- Supports async (matching existing httpx-based scrapers)
- Has good performance
- Is easy to integrate with existing code
- Supports dependency injection

**Decision**: Use **FastAPI**

**Rationale**:
- Native async support with async/await
- Automatic OpenAPI/Swagger documentation
- Pydantic models for data validation
- Dependency injection system
- Excellent performance
- Growing ecosystem
- Matches existing Python 3.11 codebase

**Alternatives Considered**:
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Flask | Simple, well-known | No native async, requires extensions | Rejected - async is critical |
| Django | Batteries included | Heavy, opinionated | Rejected - too heavy |
| FastAPI | Native async, modern | Newer framework | **Selected** |
| Starlette | Lightweight, async | Less features | Rejected - FastAPI is built on it |

---

### Decision 3: API Design Pattern

**Context**: Need to expose search functionality via API while reusing existing Pipeline

**Decision**: Use **Adapter Pattern** with Facade

**Rationale**:
- Create adapter layer that converts between API models and core models
- Facade pattern provides simple API interface to complex pipeline
- Keeps core modules unchanged
- Single responsibility: API layer handles HTTP, core handles business logic

**Implementation**:
```
web/shared/adapters.py
- SearchRequest → Pipeline input
- Listing → ItemCard
- Review → ReviewInfo
```

---

### Decision 4: Frontend-Backend Communication

**Context**: Need to transfer search results from backend to frontend

**Decision**: Use **JSON API** with server-side rendering fallback

**Rationale**:
- Initial page load: Server renders basic HTML with search bar
- Search submission: htmx sends query, receives HTML fragments
- For dynamic sorting: Can use client-side sorting or re-query
- Simple, standard approach

**Format**:
```json
{
  "query": "search term",
  "results": [
    {
      "id": "unique-id",
      "title": "Item Title",
      "price": 99.99,
      "currency": "EUR",
      "posted_date": "2025-05-20",
      "original_url": "https://...",
      "image_url": "https://...",
      "score": 0.95,
      "review_summary": "4.5/5 from 12 reviews"
    }
  ],
  "sort_options": ["score", "price_asc", "price_desc", "date"],
  "toggles": {
    "filtering": true,
    "reviewing": true
  }
}
```

---

### Decision 5: State Management for Sorting and Toggles

**Context**: Need to maintain UI state (sort order, toggle states) across interactions

**Decision**: Use **URL query parameters + localStorage**

**Rationale**:
- Sort order: `?sort=price_asc` - shareable URLs
- Toggle states: `?filtering=false&reviewing=false` - shareable URLs
- Fallback to localStorage for persistence across page refreshes
- htmx can read URL params and update UI accordingly

**Implementation**:
- Sort: URL parameter, server re-sorts
- Toggles: URL parameter, client-side state + server respect
- Hover reviews: Client-side only (from initial data)

---

### Decision 6: Error Handling Strategy

**Context**: Need to handle various error scenarios gracefully

**Decision**: Multi-level error handling

**Rationale**:
- **Client-side**: Validate input before submission
- **API level**: Return appropriate HTTP status codes
- **UI level**: Show user-friendly error messages

**Error Codes**:
| Scenario | HTTP Status | UI Message |
|----------|-------------|------------|
| Empty query | 400 | "Please enter a search term" |
| No results | 200 | "No items found matching your search" |
| Scraper timeout | 504 | "Search is taking longer than usual, please retry" |
| LLM error | 502 | "AI processing unavailable, showing unfiltered results" |
| Server error | 500 | "Something went wrong, please try again later" |

---

### Decision 7: Responsive Design Approach

**Context**: Web interface must work on desktop and mobile devices

**Decision**: Use **Mobile-First CSS with Flexbox/Grid**

**Rationale**:
- Mobile-first ensures good mobile experience
- Flexbox for 1D layouts (search bar, header)
- CSS Grid for 2D layouts (card grid)
- Media queries for breakpoint adjustments
- No framework needed for responsive layout

**Breakpoints**:
- Mobile: < 768px (single column cards)
- Tablet: 768px - 1024px (2 column cards)
- Desktop: > 1024px (3-4 column cards)

---

### Decision 8: Card Design and Layout

**Context**: Cards must display: image, title, price, posted date, original website, and show reviews on hover

**Decision**: CSS Grid with absolute positioning for hover element

**Rationale**:
- Grid provides consistent card sizing
- Absolute positioned hover element appears over card
- CSS transitions for smooth animations
- No JavaScript required for basic hover

**Card Structure**:
```html
<div class="card">
  <img src="image_url" alt="item image">
  <div class="card-content">
    <h3>Title</h3>
    <div class="price">€99.99</div>
    <div class="date">Posted: May 20, 2025</div>
    <div class="source">Vinted</div>
  </div>
  <div class="card-hover">
    <div class="review-summary">⭐ 4.5/5 (12 reviews)</div>
  </div>
</div>
```

---

### Decision 9: Search Bar Animation

**Context**: Search bar starts in middle, moves to top on validation

**Decision**: CSS Transform + Transition

**Rationale**:
- Smooth animation with CSS only
- No JavaScript required for the animation
- Can be triggered by htmx swap or class addition

**Implementation**:
```css
.search-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  transition: top 0.3s ease, transform 0.3s ease;
}
.search-container.active {
  top: 20px;
  transform: translateX(-50%);
}
```

---

### Decision 10: Deployment Strategy

**Context**: Need to deploy web interface alongside existing CLI

**Decision**: Single deployment with both CLI and web

**Rationale**:
- CLI and web share same codebase and dependencies
- Single Python environment
- FastAPI can serve both API and static files
- CLI continues to work as Python module

**Deployment Options**:
| Option | Description | Recommended |
|--------|-------------|-------------|
| Direct | `uvicorn web.backend.main:app` | For development |
| Gunicorn + Uvicorn | Production-grade WSGI | For production |
| Docker | Containerized deployment | For production |
| Systemd | Background service | For servers |


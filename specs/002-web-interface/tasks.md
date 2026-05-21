---

description: "Task list for web interface feature implementation"
---

# Tasks: Web Interface for Search Tool

**Input**: Design documents from `/specs/002-web-interface/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per constitution (Test-First means tests before implementation, but not that tests must be explicitly documented). Tests will be written as part of implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to repository root `/home/pavlo/other/second_hand_searcher/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for web interface

- [x] T001 Create web/ directory structure per implementation plan
- [x] T002 [P] Create web/backend/__init__.py with package initialization
- [x] T003 [P] Create web/backend/api/__init__.py with API package initialization
- [x] T004 [P] Create web/backend/models/__init__.py with models package initialization
- [x] T005 [P] Create web/backend/shared/__init__.py with shared package initialization
- [x] T006 [P] Create web/frontend/static/css/__init__.py placeholder
- [x] T007 [P] Create web/frontend/static/js/__init__.py placeholder
- [x] T008 [P] Create web/frontend/templates/__init__.py placeholder
- [x] T009 Install FastAPI and uvicorn dependencies
- [x] T010 Install pytest and playwright dependencies for testing

**Checkpoint**: ✅ Project structure created and dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Create web/backend/main.py FastAPI application with basic configuration
- [x] T012 [P] Create web/backend/models/schemas.py with all Pydantic models (SearchRequest, ItemResponse, ReviewResponse, SearchResponse, ErrorResponse)
- [x] T013 [P] Create web/shared/adapters.py with listing_to_item_response and item_response_to_item_card functions
- [x] T014 Create web/backend/api/search.py with search endpoint implementation
- [x] T015 [P] Create config.py web configuration extension (WebConfig class)
- [x] T016 Create .env.web template with web-specific environment variables
- [x] T017 [P] Setup CORS middleware in web/backend/main.py
- [x] T018 [P] Setup exception handlers in web/backend/main.py for ErrorResponse
- [x] T019 Create web/backend/tests/__init__.py with test package initialization
- [x] T020 Create tests/frontend/__init__.py with frontend test package initialization

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Search for Items via Web Interface (Priority: P1) 🎯 MVP

**Goal**: Enable users to search for second-hand items through a web browser and see results as cards

**Independent Test**: Can be fully tested by navigating to the web page, entering a search query, and verifying that relevant item cards are displayed with image, title, price, posted date, and original website

**Status**: ✅ IN PROGRESS - Core implementation complete

### Implementation for User Story 1

- [x] T021 [P] [US1] Create index.html in web/frontend/templates/ with search bar and results container
- [x] T022 [P] [US1] Create styles.css in web/frontend/static/css/ with search bar styling
- [x] T023 [P] [US1] Create styles.css card grid layout and card styling
- [x] T024 [P] [US1] Create styles.css search bar animation (center to top)
- [x] T025 [P] [US1] Create styles.css card hover effects for reviews
- [x] T026 [P] [US1] Create app.js in web/frontend/static/js/ with htmx initialization
- [x] T027 [US1] Implement GET /api/v1/search endpoint in web/backend/api/search.py
- [x] T028 [US1] Implement Pipeline integration in web/backend/api/search.py using adapters
- [x] T029 [US1] Implement FastAPI static files serving in web/backend/main.py
- [x] T030 [US1] Implement Jinja2 template rendering for index.html in web/backend/main.py
- [x] T031 [US1] Create web/frontend/templates/index.html with htmx search form
- [x] T032 [US1] Create web/frontend/static/js/app.js with search submission handling
- [x] T033 [US1] Create web/frontend/static/js/app.js with card rendering from API response
- [x] T034 [US1] Implement click handler for cards to redirect to original_url
- [x] T035 [US1] Add loading state and error handling in app.js
- [x] T036 [US1] Add visual feedback during search operations per FR-014

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can search and see results as cards.

---

## Phase 4: User Story 2 - Configure Search Options (Priority: P2)

**Goal**: Allow users to toggle filtering and reviewing options to customize their search experience

**Independent Test**: Can be tested by verifying that toggle controls exist on the page, can be changed, and that the search behavior adapts accordingly (filtering disabled shows unfiltered results, reviewing disabled hides review info on hover)

### Implementation for User Story 2

- [x] T037 [P] [US2] Add toggle controls UI in web/frontend/templates/index.html
- [x] T038 [P] [US2] Add toggle state management in web/frontend/static/js/app.js
- [x] T039 [P] [US2] Update styles.css with toggle button styling
- [x] T040 [US2] Add use_filter parameter support in GET /api/v1/search endpoint
- [x] T041 [US2] Add use_reviews parameter support in GET /api/v1/search endpoint
- [x] T042 [US2] Update PipelineConfig in web/backend/api/search.py to respect toggle states
- [x] T043 [US2] Update adapters.py to pass toggle states to Pipeline
- [x] T044 [US2] Add URL parameter sync for toggles in app.js
- [x] T045 [US2] Update card rendering in app.js to respect reviewing toggle

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can toggle options and see behavior change.

---

## Phase 5: User Story 3 - Sort Search Results (Priority: P2)

**Goal**: Enable users to sort search results by different criteria (score, price, posted date)

**Independent Test**: Can be tested by changing sort options and verifying the order of results changes accordingly. Verify ascending and descending price sorting works.

### Implementation for User Story 3

- [x] T046 [P] [US3] Add sort control UI in web/frontend/templates/index.html
- [x] T047 [P] [US3] Add sort state management in web/frontend/static/js/app.js
- [x] T048 [P] [US3] Update styles.css with sort control styling
- [x] T049 [US3] Add sort_by parameter support in GET /api/v1/search endpoint
- [x] T050 [US3] Implement sorting logic in web/backend/api/search.py
- [x] T051 [US3] Add server-side sorting for score, price_asc, price_desc, date
- [x] T052 [US3] Update card rendering in app.js to trigger re-sort
- [x] T053 [US3] Add URL parameter sync for sort_by in app.js

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. Users can sort results by any criterion.

---

## Phase 6: User Story 4 - Maintain CLI Functionality (Priority: P1)

**Goal**: Ensure all existing CLI functionality continues to work without modification

**Independent Test**: Can be tested by running existing CLI commands and verifying they produce the same output as before. Run CLI and web simultaneously to verify no interference.

### Implementation for User Story 4

- [x] T054 [US4] Verify second_hand_research.py imports still work with new web/ directory
- [x] T055 [US4] Run existing CLI tests to ensure no regressions
- [x] T056 [US4] Test CLI with various queries to verify functionality
- [x] T057 [US4] Run CLI and web interface simultaneously to verify independence
- [x] T058 [US4] Document CLI compatibility in quickstart.md

**Checkpoint**: CLI functionality verified as unchanged and working.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T059 [P] Add responsive design breakpoints in styles.css (mobile, tablet, desktop)
- [x] T060 [P] Handle edge cases: no results, missing images, missing data
- [x] T061 [P] Add error messages for invalid queries and server errors
- [x] T062 [P] Add fallback for missing images (placeholder image)
- [x] T063 [P] Add truncation for long titles and descriptions in cards
- [x] T064 [P] Add currency formatting helpers in app.js
- [x] T065 [P] Add date formatting helpers in app.js
- [x] T066 [P] Optimize card rendering performance for 40+ items (DocumentFragment + requestAnimationFrame + lazy loading)
- [x] T067 [P] Add loading spinner animation in styles.css
- [x] T068 [P] Create quickstart.md validation - verify all steps work
- [x] T069 Update README.md with web interface usage instructions
- [x] T070 Clean up temporary files and debug output (.gitignore updated)

---

## Phase 8: Tests (Optional per Constitution - Write Before Implementation)

**Purpose**: Comprehensive test coverage as per Test-First principle

- [x] T071 [P] [US1] Unit test for GET /api/v1/search in web/backend/tests/test_search.py
- [x] T072 [P] [US1] Unit test for adapters in web/backend/tests/test_adapters.py
- [x] T073 [P] [US1] Unit test for error handling in web/backend/tests/test_errors.py
- [x] T074 [P] [US1] Integration test for search flow in tests/integration/test_web_flow.py
- [x] T075 [P] [US2] Unit test for toggle handling in web/backend/tests/test_search.py
- [x] T076 [P] [US3] Unit test for sorting in web/backend/tests/test_search.py
- [x] T077 [P] [US4] Regression test for CLI functionality in tests/test_cli.py
- [x] T078 [P] Frontend test for search flow in tests/frontend/test_search.py
- [x] T079 [P] Frontend test for card display in tests/frontend/test_cards.py
- [x] T080 [P] Frontend test for responsive design in tests/frontend/test_responsive.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all user stories being complete
- **Tests (Phase 8)**: Can be written before or after implementation (Test-First)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for toggle UI placement
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for sort UI placement
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies, but verification happens last

### Within Each User Story

- Infrastructure before implementation
- Models before services
- Services before endpoints
- Endpoints before frontend integration
- Core implementation before polish

---

## Parallel Opportunities

### Phase 1: Setup (All tasks can run in parallel)
```bash
# All T001-T010 can run together
```

### Phase 2: Foundational (Parallel tasks)
```bash
# T012, T013, T015, T016, T017, T018, T019, T020 can run in parallel
# T011 and T014 must run sequentially
```

### Phase 3: User Story 1 (Parallel tasks)
```bash
# T021-T026 can run in parallel (frontend files)
# T027-T030 can run in parallel (backend files)
# T031-T036 must run sequentially (integration)
```

### Phase 4: User Story 2 (Parallel tasks)
```bash
# T037-T039 can run in parallel (UI)
# T040-T043 can run in parallel (backend)
# T044-T045 can run in parallel (frontend logic)
```

### Phase 5: User Story 3 (Parallel tasks)
```bash
# T046-T048 can run in parallel (UI)
# T049-T051 can run in parallel (backend)
# T052-T053 can run in parallel (frontend logic)
```

### Phase 6: User Story 4 (Sequential)
```bash
# T054-T058 must run sequentially
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Verify → Deploy/Demo
6. Add Polish → Final deployment

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T021-T036)
   - Developer B: User Story 2 (T037-T045)
   - Developer C: User Story 3 (T046-T053) + User Story 4 (T054-T058)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are written before implementation per Test-First principle (but not explicitly required in spec)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

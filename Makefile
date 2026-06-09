.PHONY: test test-backend test-frontend

test: test-backend test-frontend

test-backend:
	python -m pytest web/backend/tests/ -v

test-frontend:
	python -m pytest web/frontend/tests/ -v

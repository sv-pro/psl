.PHONY: help dev backend frontend install test clean healthcheck

# Default target
help:
	@echo "Prompt Semantic Linter - Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make dev          - Run both backend and frontend in parallel"
	@echo "  make backend      - Run backend server only"
	@echo "  make frontend     - Run frontend dev server only"
	@echo "  make install      - Install all dependencies (backend + frontend)"
	@echo "  make test         - Run all tests"
	@echo "  make healthcheck  - Check API connectivity and model availability"
	@echo "  make clean        - Clean all temporary files"
	@echo ""

# Run both backend and frontend in parallel
dev:
	@echo "Starting backend and frontend servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@trap 'kill 0' INT; \
	(cd backend && python main.py) & \
	(cd frontend && npm run dev) & \
	wait

# Run backend only
backend:
	@echo "Starting backend server on http://localhost:8000"
	cd backend && python main.py

# Run frontend only
frontend:
	@echo "Starting frontend dev server on http://localhost:5173"
	cd frontend && npm run dev

# Install all dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo ""
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "✅ All dependencies installed!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure API keys in backend/.env"
	@echo "  2. Run 'make healthcheck' to verify setup"
	@echo "  3. Run 'make dev' to start both servers"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && make test

# Health check
healthcheck:
	@echo "Checking API connectivity and model availability..."
	cd backend && make healthcheck

# Clean temporary files
clean:
	@echo "Cleaning backend..."
	cd backend && make clean
	@echo "Cleaning frontend..."
	cd frontend && rm -rf node_modules/.vite dist
	@echo "✅ Cleanup complete!"

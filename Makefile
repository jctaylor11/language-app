dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	uvicorn backend.main:app --reload

dev-frontend:
	cd frontend && npm run dev

.PHONY: dev dev-backend dev-frontend

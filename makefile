dev:
	npx concurrently \
		"uvicorn backend.main:app --reload" \
		"cd frontend && npm run dev"
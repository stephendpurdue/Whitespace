.PHONY: install ingest analyze dev-ingestion dev-analysis dev-frontend test

install:
	cd backend-ingestion && pip install -e ".[dev]"
	cd backend-analysis && pip install -e ".[dev]"
	cd frontend-dashboard && npm install

ingest:
	cd backend-ingestion && python -m ingestion.cli ingest $(ARGS)

analyze:
	cd backend-analysis && python -m analysis.cli analyze $(ARGS)

dev-ingestion:
	cd backend-ingestion && python -m ingestion.cli serve

dev-analysis:
	cd backend-analysis && python -m analysis.cli serve

dev-frontend:
	cd frontend-dashboard && npm run dev

test:
	cd backend-ingestion && pytest
	cd backend-analysis && pytest

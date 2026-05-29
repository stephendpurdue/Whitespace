"""FastAPI app — knowledge base read API for analysis + frontend."""

from __future__ import annotations

import json

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ingestion.models import Brand, BrandInput
from ingestion.pipeline import IngestionPipeline
from ingestion.settings import get_settings
from ingestion.storage import BrandRepository

get_settings()

app = FastAPI(title="Trigger Discovery — Ingestion API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateBrandRequest(BaseModel):
    name: str = Field(..., min_length=1)
    primary_domain: str = Field(..., min_length=1)
    competitor_domains: list[str] = Field(default_factory=list)
    seed_topics: list[str] = Field(default_factory=list)
    run_ingestion: bool = Field(
        default=True,
        description="When true, start crawl/extract/normalize in the background.",
    )


def _repo() -> BrandRepository:
    return BrandRepository(get_settings())


def _run_ingestion_job(brand_input: BrandInput, brand_id: str) -> None:
    data = json.loads((_repo().brand_dir(brand_id) / "brand.json").read_text())
    brand = Brand(
        brand_id=data["brand_id"],
        name=data["name"],
        primary_domain=data["primary_domain"],
        competitor_domains=data.get("competitor_domains", []),
        seed_topics=data.get("seed_topics", []),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )
    settings = get_settings()
    pipeline = IngestionPipeline(settings)
    try:
        pipeline.run(brand_input, brand=brand)
    finally:
        pipeline.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion"}


@app.get("/brands")
def list_brands() -> list[dict]:
    return _repo().list_brands()


@app.get("/brands/{brand_id}")
def get_brand(brand_id: str) -> dict:
    path = _repo().brand_dir(brand_id) / "brand.json"
    if not path.exists():
        raise HTTPException(404, "Brand not found")
    return json.loads(path.read_text())


@app.post("/brands", status_code=202)
def create_brand(
    body: CreateBrandRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    brand_input = BrandInput(
        name=body.name,
        primary_domain=body.primary_domain,
        competitor_domains=body.competitor_domains,
        seed_topics=body.seed_topics,
    )
    brand = Brand.from_input(brand_input)
    repo = _repo()
    repo.save_brand(brand.to_dict())

    if not body.run_ingestion:
        return {
            "brand_id": brand.brand_id,
            "status": "created",
            "ingestion": "skipped",
        }

    background_tasks.add_task(_run_ingestion_job, brand_input, brand.brand_id)
    ing = repo.ingestion_dir(brand.brand_id)
    ing.mkdir(parents=True, exist_ok=True)
    repo.write_batch_run(
        ing,
        {
            "batch_run_id": "pending",
            "brand_id": brand.brand_id,
            "run_type": "ingestion",
            "status": "pending",
            "started_at": brand.created_at,
            "errors": [],
        },
    )

    return {
        "brand_id": brand.brand_id,
        "status": "accepted",
        "ingestion": "started",
        "poll": f"/brands/{brand.brand_id}/batch-run",
    }


@app.get("/brands/{brand_id}/batch-run")
def get_batch_run(brand_id: str) -> dict:
    repo = _repo()
    if not repo.brand_dir(brand_id).exists():
        raise HTTPException(404, "Brand not found")
    batch = repo.read_batch_run(brand_id)
    if not batch:
        raise HTTPException(404, "No batch run for brand")
    return batch


@app.get("/brands/{brand_id}/facts")
def get_facts(brand_id: str) -> list[dict]:
    repo = _repo()
    if not repo.brand_dir(brand_id).exists():
        raise HTTPException(404, "Brand not found")
    return repo.read_jsonl(repo.ingestion_dir(brand_id) / "normalized" / "facts.jsonl")


@app.get("/brands/{brand_id}/source-pages")
def get_source_pages(brand_id: str) -> list[dict]:
    repo = _repo()
    if not repo.brand_dir(brand_id).exists():
        raise HTTPException(404, "Brand not found")
    return repo.read_jsonl(repo.ingestion_dir(brand_id) / "source_pages.jsonl")

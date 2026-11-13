from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import SearchResponse, University
from app.services import search_universities

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Uni Finder",
    description="Search universities by name or country and view their websites.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    name: str | None = Query(None),
    country: str | None = Query(None),
):
    results: list[dict] = []
    source = "none"
    searched = bool((name and name.strip()) or (country and country.strip()))

    if searched:
        results, source = await search_universities(name, country)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "name": name or "",
            "country": country or "",
            "results": results,
            "source": source,
            "searched": searched,
            "count": len(results),
        },
    )


@app.get("/api/universities", response_model=SearchResponse)
async def api_universities(
    name: str | None = Query(None, description="University name (partial match)"),
    country: str | None = Query(None, description="Country name (partial match)"),
):
    results, source = await search_universities(name, country)
    return SearchResponse(
        source=source,
        count=len(results),
        query={"name": name, "country": country},
        results=[University.model_validate(item) for item in results],
    )


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Uni Finder"}

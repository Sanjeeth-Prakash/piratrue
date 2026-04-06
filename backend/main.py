import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import (
    search_all,
    search_fitgirl,
    search_dodi,
    search_filecr,
    search_1337x,
    get_trending_games,
    get_trending_software
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "PIRATRUE API is running 🏴‍☠️"}

@app.get("/search")
async def search(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    results = await search_all(q.strip())
    return {"query": q, "count": len(results), "results": results}

@app.get("/search/games")
async def search_games(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    fitgirl, dodi = await asyncio.gather(
        search_fitgirl(q.strip()),
        search_dodi(q.strip())
    )
    results = fitgirl + dodi
    return {"query": q, "count": len(results), "results": results}

@app.get("/search/software")
async def search_software(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    results = await search_1337x(q.strip(), "Software")
    return {"query": q, "count": len(results), "results": results}

@app.get("/trending/games")
async def trending_games():
    results = await get_trending_games()
    return {"results": results}

@app.get("/trending/software")
async def trending_software():
    results = await get_trending_software()
    return {"results": results}

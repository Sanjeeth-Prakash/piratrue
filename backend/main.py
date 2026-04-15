import asyncio
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from scraper import search_fitgirl, search_software, get_trending_games, get_trending_software

app = FastAPI(title="PIRATRUE API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "PIRATRUE API running", "version": "3.0.0"}

@app.get("/search/games")
async def search_games(q: str = Query(..., min_length=2)):
    results = await search_fitgirl(q.strip())
    return {"query": q, "count": len(results), "results": results}

@app.get("/search/software")
async def search_sw(q: str = Query(..., min_length=2)):
    results = await search_software(q.strip())
    return {"query": q, "count": len(results), "results": results}

@app.get("/trending/games")
async def trending_games():
    results = await get_trending_games()
    return {"count": len(results), "results": results}

@app.get("/trending/software")
async def trending_sw():
    results = await get_trending_software()
    return {"count": len(results), "results": results}

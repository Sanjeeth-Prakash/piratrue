import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import search_fitgirl, search_dodi, search_software, get_trending_games, get_trending_software

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "PIRATRUE API running"}

@app.get("/search/games")
async def sg(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    fg, dodi = await asyncio.gather(search_fitgirl(q.strip()), search_dodi(q.strip()))
    results = fg + dodi
    return {"query": q, "count": len(results), "results": results}

@app.get("/search/software")
async def ss(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    results = await search_software(q.strip())
    return {"query": q, "count": len(results), "results": results}

@app.get("/trending/games")
async def tg():
    results = await get_trending_games()
    return {"results": results}

@app.get("/trending/software")
async def ts():
    results = await get_trending_software()
    return {"results": results}

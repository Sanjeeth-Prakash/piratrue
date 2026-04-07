import asyncio
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from scraper import (
    search_fitgirl,
    search_dodi,
    search_software,
    get_trending_games,
    get_trending_software,
)

app = FastAPI(title="PIRATRUE API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "PIRATRUE API running",
        "version": "2.0.0",
        "endpoints": {
            "game_search":       "/search/games?q=<query>",
            "software_search":   "/search/software?q=<query>",
            "trending_games":    "/trending/games",
            "trending_software": "/trending/software",
        },
    }


@app.get("/search/games")
async def search_games(q: str = Query(..., min_length=2)):
    """
    Search FitGirl + DODI repacks concurrently.

    Each result contains:
      - torrent_url  → direct .torrent file or magnet link (use for the download button)
      - post_url     → original repack site post       (use for the "Visit Site" button)
      - magnet       → True if torrent_url is a magnet link, False if it's a .torrent file
    """
    q = q.strip()
    fg, dodi = await asyncio.gather(search_fitgirl(q), search_dodi(q))
    results = fg + dodi
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/search/software")
async def search_software_endpoint(q: str = Query(..., min_length=2)):
    """
    Search The Pirate Bay for software.
    Only returns purple (VIP/Trusted) and green (Admin) skull uploads.

    Each result contains:
      - torrent_url  → magnet link ready for your torrent client
      - post_url     → TPB description page  (use for the "Visit Site" button)
      - skull        → 👑 VIP / 🟣 Trusted / 🟢 Admin
      - trusted      → always True (non-trusted posts are filtered out)
    """
    results = await search_software(q.strip())
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/trending/games")
async def trending_games():
    """Latest repacks from FitGirl homepage with direct torrent links."""
    results = await get_trending_games()
    return {"count": len(results), "results": results}


@app.get("/trending/software")
async def trending_software():
    """Trending trusted software from The Pirate Bay."""
    results = await get_trending_software()
    return {"count": len(results), "results": results}

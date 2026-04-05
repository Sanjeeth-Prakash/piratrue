from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import search_all

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "PIRATRUE API is running"}

@app.get("/search")
async def search(q: str):
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q}
    results = await search_all(q.strip())
    return {
        "query": q,
        "count": len(results),
        "results": results
    }
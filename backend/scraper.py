import httpx
from bs4 import BeautifulSoup
import asyncio
import random
import urllib.parse

AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def H():
    return {
        "User-Agent": random.choice(AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

async def _fg_torrent(url: str, client: httpx.AsyncClient) -> dict:
    """Grab torrent/magnet from a FitGirl post page."""
    try:
        r = await client.get(url, headers=H(), timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        t = soup.find("a", href=lambda h: h and h.endswith(".torrent"))
        if t:
            return {"link": t["href"], "magnet": False}
        m = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if m:
            return {"link": m["href"], "magnet": True}
    except Exception as e:
        print(f"FG torrent error: {e}")
    return {"link": url, "magnet": False}


async def search_fitgirl(query: str):
    results = []
    try:
        url = f"https://fitgirl-repacks.site/?s={urllib.parse.quote_plus(query)}"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, headers=H())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:6]
            items = []
            for p in posts:
                t = p.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                size = "N/A"
                s = p.find(string=lambda x: x and "GB" in x)
                if s:
                    size = s.strip()[:25]
                img = p.select_one("img")
                items.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("data-src") or img.get("src") or "" if img else "",
                })
            links = await asyncio.gather(*[_fg_torrent(i["post_url"], client) for i in items])
            for item, lnk in zip(items, links):
                results.append({
                    "title": item["title"],
                    "link": lnk["link"],
                    "post_url": item["post_url"],
                    "size": item["size"],
                    "seeds": "N/A",
                    "image": item["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": lnk["magnet"],
                })
    except Exception as e:
        print(f"FitGirl search error: {e}")
    return results


async def get_trending_games():
    results = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get("https://fitgirl-repacks.site/", headers=H())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:8]
            items = []
            for p in posts:
                t = p.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                size = "N/A"
                s = p.find(string=lambda x: x and "GB" in x)
                if s:
                    size = s.strip()[:25]
                img = p.select_one("img")
                items.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("data-src") or img.get("src") or "" if img else "",
                })
            links = await asyncio.gather(*[_fg_torrent(i["post_url"], client) for i in items])
            for item, lnk in zip(items, links):
                results.append({
                    "title": item["title"],
                    "link": lnk["link"],
                    "post_url": item["post_url"],
                    "size": item["size"],
                    "seeds": "N/A",
                    "image": item["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": lnk["magnet"],
                })
    except Exception as e:
        print(f"FitGirl trending error: {e}")
    return results


BAD = {'xxx','porn','sex','hentai','jav','anal','creampie','uncensored','mosaic','erotic'}

def _safe(title: str) -> bool:
    l = title.lower()
    return not any(b in l for b in BAD) and not any(0x3000 <= ord(c) <= 0x9FFF for c in title)


async def search_software(query: str):
    """Knaben public API — works from any server IP."""
    results = []
    try:
        payload = {
            "search_type": "all",
            "search_field": "title",
            "query": f"{query} crack activated",
            "size": 20,
            "from": 0,
            "orderBy": "seeders",
            "order": "desc"
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.knaben.eu/v1",
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": random.choice(AGENTS)}
            )
        data = r.json()
        hits = [x for x in (data.get("hits") or []) if _safe(x.get("title", ""))][:10]
        for x in hits:
            b = int(x.get("bytes", 0))
            gb = round(b / 1_073_741_824, 2)
            size = f"{gb} GB" if gb >= 1 else f"{round(b/1_048_576, 1)} MB"
            mag = f"magnet:?xt=urn:btih:{x['hash']}&dn={urllib.parse.quote_plus(x['title'])}&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337"
            results.append({
                "title": x["title"],
                "link": mag,
                "size": size,
                "seeds": str(x.get("seeders", 0)),
                "image": "",
                "source": "Knaben",
                "skull": "🟢",
                "magnet": True,
            })
    except Exception as e:
        print(f"Knaben error: {e}")
    return results


async def get_trending_software():
    queries = [
        "adobe photoshop 2024 crack",
        "microsoft office 2024 activated",
        "autocad 2024 crack",
        "windows 11 activated",
    ]
    seen = set()
    all_results = []
    groups = await asyncio.gather(*[search_software(q) for q in queries])
    for group in groups:
        for item in group:
            if item["link"] not in seen:
                seen.add(item["link"])
                all_results.append(item)
    all_results.sort(key=lambda x: int(x.get("seeds", 0)), reverse=True)
    return all_results[:12]

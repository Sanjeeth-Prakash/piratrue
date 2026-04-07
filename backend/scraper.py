import httpx
from bs4 import BeautifulSoup
import asyncio
import random

AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def headers():
    return {
        "User-Agent": random.choice(AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


async def get_fitgirl_magnet(post_url: str, client: httpx.AsyncClient) -> str:
    try:
        r = await client.get(post_url, headers=headers(), timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        magnet = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if magnet:
            return magnet["href"]
    except Exception as e:
        print(f"Magnet fetch error: {e}")
    return post_url


async def search_fitgirl(query: str):
    results = []
    try:
        url = f"https://fitgirl-repacks.site/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers=headers())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:5]
            post_data = []
            for post in posts:
                t = post.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                size = "N/A"
                se = post.find(string=lambda x: x and "GB" in x)
                if se:
                    size = se.strip()[:20]
                img = post.select_one("img")
                post_data.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("src", "") if img else "",
                })
            magnets = await asyncio.gather(*[get_fitgirl_magnet(p["post_url"], client) for p in post_data])
            for p, mag in zip(post_data, magnets):
                results.append({
                    "title": p["title"],
                    "link": mag,
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": mag.startswith("magnet:")
                })
    except Exception as e:
        print(f"FitGirl error: {e}")
    return results


async def search_dodi(query: str):
    results = []
    try:
        url = f"https://dodi-repacks.site/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers=headers())
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("article.post")[:5]
        for post in posts:
            t = post.select_one("h1.entry-title a, h2.entry-title a")
            if not t:
                continue
            img = post.select_one("img")
            results.append({
                "title": t.text.strip(),
                "link": t["href"],
                "size": "N/A",
                "seeds": "N/A",
                "image": img.get("src", "") if img else "",
                "source": "DODI",
                "skull": "🟢",
                "magnet": False
            })
    except Exception as e:
        print(f"DODI error: {e}")
    return results


async def get_trending_games():
    results = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get("https://fitgirl-repacks.site/", headers=headers())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:8]
            post_data = []
            for post in posts:
                t = post.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                size = "N/A"
                se = post.find(string=lambda x: x and "GB" in x)
                if se:
                    size = se.strip()[:20]
                img = post.select_one("img")
                post_data.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("src", "") if img else "",
                })
            magnets = await asyncio.gather(*[get_fitgirl_magnet(p["post_url"], client) for p in post_data])
            for p, mag in zip(post_data, magnets):
                results.append({
                    "title": p["title"],
                    "link": mag,
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": mag.startswith("magnet:")
                })
    except Exception as e:
        print(f"Trending games error: {e}")
    return results


async def search_software(query: str):
    """Knaben public API — works from any server"""
    results = []
    try:
        BAD = ['xxx','porn','sex','hentai','jav','anal','creampie','uncensored','mosaic']
        def safe(t):
            l = t.lower()
            return not any(b in l for b in BAD) and not any(0x3000 <= ord(c) <= 0x9fff for c in t)

        payload = {
            "search_type": "all",
            "search_field": "title",
            "query": query + " crack activated",
            "size": 20,
            "from": 0,
            "orderBy": "seeders",
            "order": "desc"
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post("https://api.knaben.eu/v1", json=payload,
                headers={"Content-Type": "application/json", "User-Agent": random.choice(AGENTS)})
        data = r.json()
        hits = [x for x in (data.get("hits") or []) if safe(x.get("title", ""))][:10]
        for x in hits:
            b = int(x.get("bytes", 0))
            gb = round(b / 1073741824, 2)
            size = f"{gb} GB" if gb >= 1 else f"{round(b/1048576, 1)} MB"
            mag = f"magnet:?xt=urn:btih:{x['hash']}&dn={x['title']}&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337"
            results.append({
                "title": x["title"],
                "link": mag,
                "size": size,
                "seeds": str(x.get("seeders", 0)),
                "image": "",
                "source": "Knaben",
                "skull": "🟢",
                "magnet": True
            })
    except Exception as e:
        print(f"Knaben error: {e}")
    return results


async def get_trending_software():
    return await search_software("adobe photoshop office autocad windows")

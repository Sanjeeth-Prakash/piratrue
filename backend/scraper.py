import httpx
from bs4 import BeautifulSoup
import asyncio
import random

# Rotate user agents to avoid blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Cache-Control": "no-cache",
    }

# 1337x mirrors — tries each until one works
MIRRORS_1337X = [
    "https://1337x.to",
    "https://1337x.st",
    "https://x1337x.se",
    "https://1337x.is",
    "https://1337x.gd",
]


async def fetch_1337x(path: str) -> str:
    for mirror in MIRRORS_1337X:
        try:
            url = f"{mirror}{path}"
            async with httpx.AsyncClient(headers=get_headers(), timeout=15, follow_redirects=True) as client:
                r = await client.get(url)
                if r.status_code == 200 and len(r.text) > 500:
                    return r.text
        except Exception as e:
            print(f"Mirror {mirror} failed: {e}")
            continue
    return ""


async def get_1337x_magnet(torrent_path: str) -> str:
    html = await fetch_1337x(torrent_path)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        magnet = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if magnet:
            return magnet["href"]
    return ""


async def search_1337x(query: str, category: str = "Software", limit: int = 8):
    results = []
    try:
        path = f"/category-search/{query.replace(' ', '%20')}/{category}/1/"
        html = await fetch_1337x(path)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.table-list tbody tr")[:limit]
        tasks = []
        row_data = []
        for row in rows:
            name_els = row.select("td.name a")
            if len(name_els) < 2:
                continue
            title = name_els[1].text.strip()
            path2 = name_els[1]["href"]
            size_el = row.select_one("td.size")
            size = size_el.text.strip().split("\n")[0] if size_el else "N/A"
            seeds_el = row.select_one("td.seeds")
            seeds = seeds_el.text.strip() if seeds_el else "0"
            tasks.append(get_1337x_magnet(path2))
            row_data.append({"title": title, "size": size, "seeds": seeds})
        magnets = await asyncio.gather(*tasks)
        for d, magnet in zip(row_data, magnets):
            if not magnet:
                continue
            results.append({
                "title": d["title"],
                "link": magnet,
                "size": d["size"],
                "seeds": d["seeds"],
                "image": "",
                "source": "1337x",
                "skull": "🟢",
                "magnet": True
            })
    except Exception as e:
        print(f"1337x search error: {e}")
    return results


async def trending_1337x(category: str = "Software", limit: int = 12):
    results = []
    try:
        html = await fetch_1337x("/top-100")
        if not html:
            return await search_1337x("adobe office photoshop", category, limit)
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.table-list tbody tr")
        tasks = []
        row_data = []
        for row in rows:
            cat_el = row.select_one("td.coll-1 a")
            if not cat_el or category.lower() not in cat_el.text.lower():
                continue
            name_els = row.select("td.name a")
            if len(name_els) < 2:
                continue
            title = name_els[1].text.strip()
            path = name_els[1]["href"]
            size_el = row.select_one("td.size")
            size = size_el.text.strip().split("\n")[0] if size_el else "N/A"
            seeds_el = row.select_one("td.seeds")
            seeds = seeds_el.text.strip() if seeds_el else "0"
            tasks.append(get_1337x_magnet(path))
            row_data.append({"title": title, "size": size, "seeds": seeds})
            if len(tasks) >= limit:
                break
        if not tasks:
            return await search_1337x("adobe office photoshop", category, limit)
        magnets = await asyncio.gather(*tasks)
        for d, magnet in zip(row_data, magnets):
            if not magnet:
                continue
            results.append({
                "title": d["title"],
                "link": magnet,
                "size": d["size"],
                "seeds": d["seeds"],
                "image": "",
                "source": "1337x",
                "skull": "🟢",
                "magnet": True
            })
    except Exception as e:
        print(f"1337x trending error: {e}")
    return results


async def get_fitgirl_magnet(post_url: str, client: httpx.AsyncClient) -> str:
    try:
        r = await client.get(post_url, headers=get_headers())
        soup = BeautifulSoup(r.text, "html.parser")
        magnet = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if magnet:
            return magnet["href"]
    except Exception as e:
        print(f"Magnet extract error: {e}")
    return post_url


async def search_fitgirl(query: str):
    results = []
    try:
        url = f"https://fitgirl-repacks.site/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient(headers=get_headers(), timeout=15, follow_redirects=True) as client:
            r = await client.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:5]
            post_data = []
            for post in posts:
                title_el = post.select_one("h1.entry-title a, h2.entry-title a")
                if not title_el:
                    continue
                size = "N/A"
                size_el = post.find(string=lambda t: t and "GB" in t)
                if size_el:
                    size = size_el.strip()[:20]
                img_el = post.select_one("img")
                img = img_el.get("src", "") if img_el else ""
                post_data.append({
                    "title": title_el.text.strip(),
                    "post_url": title_el["href"],
                    "size": size,
                    "image": img,
                })
            magnets = await asyncio.gather(*[get_fitgirl_magnet(p["post_url"], client) for p in post_data])
            for p, magnet in zip(post_data, magnets):
                results.append({
                    "title": p["title"],
                    "link": magnet,
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": magnet.startswith("magnet:")
                })
    except Exception as e:
        print(f"FitGirl error: {e}")
    return results


async def search_dodi(query: str):
    results = []
    try:
        url = f"https://dodi-repacks.site/?s={query.replace(' ', '+')}"
        async with httpx.AsyncClient(headers=get_headers(), timeout=15, follow_redirects=True) as client:
            r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("article.post")[:5]
        for post in posts:
            title_el = post.select_one("h1.entry-title a, h2.entry-title a")
            if not title_el:
                continue
            img_el = post.select_one("img")
            img = img_el.get("src", "") if img_el else ""
            results.append({
                "title": title_el.text.strip(),
                "link": title_el["href"],
                "size": "N/A",
                "seeds": "N/A",
                "image": img,
                "source": "DODI",
                "skull": "🟢",
                "magnet": False
            })
    except Exception as e:
        print(f"DODI error: {e}")
    return results


async def search_filecr(query: str):
    return await search_1337x(query, "Software")


async def search_all(query: str):
    fitgirl, dodi, software = await asyncio.gather(
        search_fitgirl(query),
        search_dodi(query),
        search_1337x(query, "Software")
    )
    return fitgirl + dodi + software


async def get_trending_games():
    return await _fitgirl_home()


async def _fitgirl_home():
    results = []
    try:
        async with httpx.AsyncClient(headers=get_headers(), timeout=15, follow_redirects=True) as client:
            r = await client.get("https://fitgirl-repacks.site/")
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:8]
            post_data = []
            for post in posts:
                title_el = post.select_one("h1.entry-title a, h2.entry-title a")
                if not title_el:
                    continue
                img_el = post.select_one("img")
                img = img_el.get("src", "") if img_el else ""
                size = "N/A"
                size_el = post.find(string=lambda t: t and "GB" in t)
                if size_el:
                    size = size_el.strip()[:20]
                post_data.append({
                    "title": title_el.text.strip(),
                    "post_url": title_el["href"],
                    "size": size,
                    "image": img,
                })
            magnets = await asyncio.gather(*[get_fitgirl_magnet(p["post_url"], client) for p in post_data])
            for p, magnet in zip(post_data, magnets):
                results.append({
                    "title": p["title"],
                    "link": magnet,
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": magnet.startswith("magnet:")
                })
    except Exception as e:
        print(f"FitGirl home error: {e}")
    return results


async def get_trending_software():
    return await trending_1337x("Software", 12)

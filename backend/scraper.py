import httpx
from bs4 import BeautifulSoup
import asyncio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

CAT_SOFTWARE = 300
CAT_GAMES    = 400

TRUSTED_STATUS = {"vip", "trusted"}


def build_magnet(info_hash: str, name: str) -> str:
    trackers = (
        "&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337"
        "&tr=udp%3A%2F%2Fopen.tracker.cl%3A1337"
        "&tr=udp%3A%2F%2F9.rarbg.com%3A2810"
        "&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A6969"
    )
    return f"magnet:?xt=urn:btih:{info_hash}&dn={name}{trackers}"


def format_size(size_bytes: int) -> str:
    size_gb = round(size_bytes / (1024**3), 2)
    if size_gb >= 1:
        return f"{size_gb} GB"
    return f"{round(size_bytes / (1024**2), 1)} MB"


def parse_tpb_item(item: dict) -> dict:
    size_bytes = int(item.get("size", 0))
    info_hash = item.get("info_hash", "")
    name = item.get("name", "")
    status = item.get("status", "")
    skull = "🟢" if status == "vip" else "🟣" if status == "trusted" else "⚪"
    return {
        "title": name,
        "link": build_magnet(info_hash, name),
        "size": format_size(size_bytes),
        "seeds": str(item.get("seeders", 0)),
        "image": "",
        "source": "TPB",
        "status": status,
        "skull": skull,
        "magnet": True
    }


async def tpb_search(query: str, category: int, limit: int = 8, trusted_only: bool = True):
    results = []
    try:
        url = f"https://apibay.org/q.php?q={query.replace(' ', '+')}&cat={category}"
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            r = await client.get(url)
        data = r.json()
        if not data or (len(data) == 1 and data[0].get("id") == "0"):
            return []
        for item in data:
            if trusted_only and item.get("status", "") not in TRUSTED_STATUS:
                continue
            results.append(parse_tpb_item(item))
            if len(results) >= limit:
                break
        if not results and trusted_only:
            print(f"No trusted results for '{query}', falling back to all")
            for item in data[:limit]:
                results.append(parse_tpb_item(item))
    except Exception as e:
        print(f"TPB search error: {e}")
    return results


async def tpb_trending(category: int, limit: int = 12, trusted_only: bool = True):
    results = []
    try:
        url = f"https://apibay.org/precompiled/data_top100_{category}.json"
        async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
            r = await client.get(url)
        data = r.json()
        for item in data:
            if trusted_only and item.get("status", "") not in TRUSTED_STATUS:
                continue
            results.append(parse_tpb_item(item))
            if len(results) >= limit:
                break
        if not results and trusted_only:
            for item in data[:limit]:
                results.append(parse_tpb_item(item))
    except Exception as e:
        print(f"TPB trending error: {e}")
    return results


async def get_fitgirl_magnet(post_url: str, client: httpx.AsyncClient) -> str:
    try:
        r = await client.get(post_url)
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
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
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
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
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
    return await tpb_search(query, CAT_SOFTWARE, trusted_only=True)


async def search_all(query: str):
    fitgirl, dodi, software = await asyncio.gather(
        search_fitgirl(query),
        search_dodi(query),
        tpb_search(query, CAT_SOFTWARE, trusted_only=True)
    )
    return fitgirl + dodi + software


async def get_trending_games():
    fitgirl, tpb = await asyncio.gather(
        _fitgirl_home(),
        tpb_trending(CAT_GAMES, 6, trusted_only=True)
    )
    return fitgirl + tpb


async def _fitgirl_home():
    results = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
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
    return await tpb_trending(CAT_SOFTWARE, 12, trusted_only=True)

import httpx
from bs4 import BeautifulSoup
import asyncio
import random
import urllib.parse

# ---------------------------------------------------------------------------
# User-Agent pool
# ---------------------------------------------------------------------------
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# TPB mirrors to try in order
TPB_MIRRORS = [
    "https://apibay.org",
    "https://thepiratebay.org",
]

# Trackers appended to magnet links built from TPB info-hashes
TPB_TRACKERS = (
    "&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce"
    "&tr=udp%3A%2F%2Fopen.tracker.cl%3A1337%2Fannounce"
    "&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A6969%2Fannounce"
    "&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce"
)

# ---------------------------------------------------------------------------
# TPB status codes for trusted uploaders
#   status == 1  → VIP (purple skull)  ✅
#   status == 2  → Trusted (pink)      ✅
#   status == 3  → Admin (green skull) ✅
# Anything else (0 = normal) is skipped.
# ---------------------------------------------------------------------------
TPB_TRUSTED_STATUSES = {1, 2, 3}

# Software-related categories the NSFW filter keeps out
_BAD_WORDS = {
    'xxx', 'porn', 'sex', 'hentai', 'jav', 'anal',
    'creampie', 'uncensored', 'mosaic', 'erotic',
}


def _headers():
    return {
        "User-Agent": random.choice(AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def _is_safe_title(title: str) -> bool:
    """Return True when the title contains no adult keywords or CJK spam."""
    low = title.lower()
    return (
        not any(b in low for b in _BAD_WORDS)
        and not any(0x3000 <= ord(c) <= 0x9FFF for c in title)
    )


# ---------------------------------------------------------------------------
# FitGirl helpers
# ---------------------------------------------------------------------------

async def _fitgirl_torrent_from_post(post_url: str, client: httpx.AsyncClient) -> dict:
    """
    Visit a FitGirl post page and return:
      - torrent_url  : direct .torrent file URL (preferred) or magnet link
      - magnet       : True/False
    """
    torrent_url = post_url   # fallback: send user to the post page
    is_magnet = False
    try:
        r = await client.get(post_url, headers=_headers(), timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        # 1️⃣  Prefer a .torrent direct download link
        torrent_tag = soup.find("a", href=lambda h: h and h.endswith(".torrent"))
        if torrent_tag:
            torrent_url = torrent_tag["href"]
            is_magnet = False
            return {"torrent_url": torrent_url, "magnet": is_magnet}

        # 2️⃣  Fall back to magnet link
        magnet_tag = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if magnet_tag:
            torrent_url = magnet_tag["href"]
            is_magnet = True
            return {"torrent_url": torrent_url, "magnet": is_magnet}

    except Exception as e:
        print(f"[FitGirl] torrent fetch error for {post_url}: {e}")

    return {"torrent_url": torrent_url, "magnet": is_magnet}


async def _dodi_torrent_from_post(post_url: str, client: httpx.AsyncClient) -> dict:
    """
    Visit a DODI post and return torrent_url + magnet flag.
    DODI typically uses 1fichier / Google Drive links, but may also have
    magnet or .torrent links — we grab whichever is available.
    """
    torrent_url = post_url
    is_magnet = False
    try:
        r = await client.get(post_url, headers=_headers(), timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")

        torrent_tag = soup.find("a", href=lambda h: h and h.endswith(".torrent"))
        if torrent_tag:
            return {"torrent_url": torrent_tag["href"], "magnet": False}

        magnet_tag = soup.find("a", href=lambda h: h and h.startswith("magnet:"))
        if magnet_tag:
            return {"torrent_url": magnet_tag["href"], "magnet": True}

    except Exception as e:
        print(f"[DODI] torrent fetch error for {post_url}: {e}")

    return {"torrent_url": torrent_url, "magnet": is_magnet}


# ---------------------------------------------------------------------------
# FitGirl search
# ---------------------------------------------------------------------------

async def search_fitgirl(query: str):
    results = []
    try:
        url = f"https://fitgirl-repacks.site/?s={urllib.parse.quote_plus(query)}"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, headers=_headers())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:6]

            post_data = []
            for post in posts:
                t = post.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                size = "N/A"
                se = post.find(string=lambda x: x and "GB" in x)
                if se:
                    size = se.strip()[:25]
                img = post.select_one("img")
                post_data.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("data-src") or img.get("src") or "" if img else "",
                })

            # Fetch torrent/magnet links concurrently
            dl_info = await asyncio.gather(
                *[_fitgirl_torrent_from_post(p["post_url"], client) for p in post_data]
            )

            for p, dl in zip(post_data, dl_info):
                results.append({
                    "title": p["title"],
                    "torrent_url": dl["torrent_url"],   # direct .torrent or magnet
                    "post_url": p["post_url"],           # "Visit Site" button target
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": dl["magnet"],
                })
    except Exception as e:
        print(f"[FitGirl] search error: {e}")
    return results


# ---------------------------------------------------------------------------
# DODI search
# ---------------------------------------------------------------------------

async def search_dodi(query: str):
    results = []
    try:
        url = f"https://dodi-repacks.site/?s={urllib.parse.quote_plus(query)}"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, headers=_headers())
            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select("article.post")[:6]

            post_data = []
            for post in posts:
                t = post.select_one("h1.entry-title a, h2.entry-title a")
                if not t:
                    continue
                img = post.select_one("img")
                post_data.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "image": img.get("data-src") or img.get("src") or "" if img else "",
                })

            dl_info = await asyncio.gather(
                *[_dodi_torrent_from_post(p["post_url"], client) for p in post_data]
            )

            for p, dl in zip(post_data, dl_info):
                results.append({
                    "title": p["title"],
                    "torrent_url": dl["torrent_url"],
                    "post_url": p["post_url"],
                    "size": "N/A",
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "DODI",
                    "skull": "🟢",
                    "magnet": dl["magnet"],
                })
    except Exception as e:
        print(f"[DODI] search error: {e}")
    return results


# ---------------------------------------------------------------------------
# Trending games (FitGirl homepage)
# ---------------------------------------------------------------------------

async def get_trending_games():
    results = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get("https://fitgirl-repacks.site/", headers=_headers())
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
                    size = se.strip()[:25]
                img = post.select_one("img")
                post_data.append({
                    "title": t.text.strip(),
                    "post_url": t["href"],
                    "size": size,
                    "image": img.get("data-src") or img.get("src") or "" if img else "",
                })

            dl_info = await asyncio.gather(
                *[_fitgirl_torrent_from_post(p["post_url"], client) for p in post_data]
            )

            for p, dl in zip(post_data, dl_info):
                results.append({
                    "title": p["title"],
                    "torrent_url": dl["torrent_url"],
                    "post_url": p["post_url"],
                    "size": p["size"],
                    "seeds": "N/A",
                    "image": p["image"],
                    "source": "FitGirl",
                    "skull": "🟢",
                    "magnet": dl["magnet"],
                })
    except Exception as e:
        print(f"[FitGirl] trending error: {e}")
    return results


# ---------------------------------------------------------------------------
# TPB software search  (purple VIP + green admin only)
# ---------------------------------------------------------------------------

def _tpb_magnet(info_hash: str, name: str) -> str:
    dn = urllib.parse.quote_plus(name)
    return f"magnet:?xt=urn:btih:{info_hash}&dn={dn}{TPB_TRACKERS}"


def _skull_label(status: int) -> str:
    return {1: "👑 VIP", 2: "🟣 Trusted", 3: "🟢 Admin"}.get(status, "⚪ Unknown")


async def _tpb_api_search(query: str, client: httpx.AsyncClient) -> list:
    """
    Query apibay.org (TPB's official JSON API) and return raw hit list.
    Falls back to thepiratebay.org if apibay is down.
    """
    encoded = urllib.parse.quote_plus(query)
    # cat=0 = all, we filter by status afterwards
    endpoints = [
        f"https://apibay.org/q.php?q={encoded}&cat=0",
        f"https://apibay.org/q.php?q={encoded}",
    ]
    for ep in endpoints:
        try:
            r = await client.get(ep, headers=_headers(), timeout=12)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    return data
        except Exception as e:
            print(f"[TPB] API error ({ep}): {e}")
    return []


async def search_software(query: str):
    results = []
    try:
        search_query = f"{query} crack activated"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            hits = await _tpb_api_search(search_query, client)

        # Filter: trusted uploaders only + safe title
        trusted = [
            h for h in hits
            if int(h.get("status", 0)) in TPB_TRUSTED_STATUSES
            and _is_safe_title(h.get("name", ""))
        ]

        # Sort by seeders descending, take top 10
        trusted.sort(key=lambda h: int(h.get("seeders", 0)), reverse=True)
        trusted = trusted[:10]

        for h in trusted:
            name = h.get("name", "Unknown")
            info_hash = h.get("info_hash", "")
            seeders = int(h.get("seeders", 0))
            leechers = int(h.get("leechers", 0))
            size_bytes = int(h.get("size", 0))
            status = int(h.get("status", 0))
            uploader = h.get("username", "")

            # Human-readable size
            if size_bytes >= 1_073_741_824:
                size_str = f"{round(size_bytes / 1_073_741_824, 2)} GB"
            elif size_bytes >= 1_048_576:
                size_str = f"{round(size_bytes / 1_048_576, 1)} MB"
            else:
                size_str = f"{size_bytes} B"

            magnet = _tpb_magnet(info_hash, name)
            tpb_link = f"https://thepiratebay.org/description.php?id={h.get('id', '')}"

            results.append({
                "title": name,
                "torrent_url": magnet,
                "post_url": tpb_link,          # "Visit Site" button → TPB page
                "size": size_str,
                "seeds": str(seeders),
                "leechers": str(leechers),
                "image": "",
                "source": "ThePirateBay",
                "skull": _skull_label(status),
                "uploader": uploader,
                "magnet": True,
                "trusted": True,
            })
    except Exception as e:
        print(f"[TPB] search error: {e}")
    return results


# ---------------------------------------------------------------------------
# Trending software
# ---------------------------------------------------------------------------

async def get_trending_software():
    """Return trusted TPB results for popular software titles."""
    queries = [
        "adobe photoshop 2024 crack",
        "microsoft office 2024 activated",
        "autocad 2024 crack",
        "windows 11 activated",
    ]
    all_results = []
    seen_hashes = set()

    async def _fetch(q):
        res = await search_software(q)
        return res

    groups = await asyncio.gather(*[_fetch(q) for q in queries])
    for group in groups:
        for item in group:
            key = item["torrent_url"]
            if key not in seen_hashes:
                seen_hashes.add(key)
                all_results.append(item)

    # Re-sort combined list by seed count
    all_results.sort(key=lambda x: int(x.get("seeds", 0)), reverse=True)
    return all_results[:12]

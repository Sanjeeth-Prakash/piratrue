<div align="center">

```
██████╗ ██╗██████╗  █████╗ ████████╗██████╗ ██╗   ██╗███████╗
██╔══██╗██║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██║   ██║██╔════╝
██████╔╝██║██████╔╝███████║   ██║   ██████╔╝██║   ██║█████╗  
██╔═══╝ ██║██╔══██╗██╔══██║   ██║   ██╔══██╗██║   ██║██╔══╝  
██║     ██║██║  ██║██║  ██║   ██║   ██║  ██║╚██████╔╝███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

**Piracy Is True Freedom.**  
*Because if buying doesn't mean owning, piracy isn't stealing.*

[![Live Site](https://img.shields.io/badge/LIVE%20SITE-piratrue-e63946?style=for-the-badge&logo=github)](https://sanjeeth-prakash.github.io/piratrue/piratrue.html)
![Status](https://img.shields.io/badge/status-active-22c55e?style=for-the-badge)
![No Files Hosted](https://img.shields.io/badge/files%20hosted-0-444?style=for-the-badge)
![Free Forever](https://img.shields.io/badge/cost-free%20forever-e63946?style=for-the-badge)

</div>

---

## What is PIRATRUE?

A free media aggregator for broke people. One site to find games, software, movies, music, books and more — all free, all clean, no malware.

PIRATRUE doesn't host a single file. It aggregates and links to trusted sources so you spend less time searching sketchy sites and more time actually downloading.

Inspired by [FMHY](https://fmhy.net) but with a brutalist design identity and live search built in.

---

## Features

| Feature | How it works |
|---|---|
| 🎮 **Game Repacks** | Live search via The Pirate Bay `cat=400`, filtered to FitGirl uploads |
| 🛠️ **Software & Cracks** | Live search via The Pirate Bay `cat=300`, VIP/Trusted/Admin only |
| 🎬 **Streaming** | Curated list of free streaming sites |
| 🎵 **Music** | Free streaming and download tools |
| 📚 **Books** | LibGen, Z-Library, Anna's Archive and more |
| 🛡️ **Privacy & Adblock** | Essential tools before you do anything online |
| 📱 **Android & iOS** | Modded APKs, ReVanced, sideloading guides |
| 🤖 **AI Tools** | Free AI chatbots and image generators |
| 🌊 **Torrenting** | Client downloads and indexer links |
| ☠️ **Unsafe Sites** | Malware blacklist sourced from FMHY |

---

## How the search works

### Game Repacks
```
User searches "Red Dead Redemption"
        ↓
apibay.org/q.php?q=red+dead+redemption&cat=400
        ↓
Filter results where username = "fitgirl"
        ↓
Sort by seeders → return magnet links
```

### Software & Cracks
```
User searches "Photoshop"
        ↓
apibay.org/q.php?q=photoshop+crack&cat=300
        ↓
Filter: status >= 1 (VIP / Trusted / Admin only)
        ↓
Sort by seeders → return magnet links
```

The seed count dots you see on results:
- 🟢 **Green** = 100+ seeders — fast download
- 🟡 **Yellow** = 10–100 seeders — slower but works
- ⚫ **Grey** = 0 seeders — dead

---

## Tech stack

```
Frontend    →  Pure HTML/CSS/JS — single file, no frameworks
Hosting     →  GitHub Pages (free)
Game search →  apibay.org JSON API (browser-side, no backend)
SW search   →  apibay.org JSON API (browser-side, no backend)
CORS proxy  →  corsproxy.io as fallback
Backend     →  FastAPI on Render (for enhanced FitGirl magnet extraction)
```

Zero dependencies. No npm. No build step. Just one HTML file.

---

## Run locally

```bash
# Just open the file — no server needed
open piratrue.html
```

For the backend (optional):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Deploy your own

1. Fork this repo
2. Go to **Settings → Pages**
3. Set source to `main` branch, root directory
4. Your site is live at `https://yourusername.github.io/piratrue/piratrue.html`

---

## Unsafe sites list

The ☠️ Unsafe Sites page lists sites confirmed to distribute malware — OceanOfGames, IGG Games, FileCR, GetIntoPC, SadeemPC, uTorrent and more.

Source: [FMHY Unsafe Sites](https://fmhy.net/unsafesites) + community reports.

Install [FMHY SafeGuard](https://github.com/fmhy/FMHY-SafeGuard) to get these flagged automatically in your browser.

---

## Disclaimer

PIRATRUE does not host, store, or distribute any copyrighted content. All links point to external third-party sources. This project is for educational and informational purposes only. Use at your own risk and in accordance with the laws of your country.

---

<div align="center">

**PIRA`TRUE`** — this site does not host any files.

*Made for broke people everywhere.*

</div>

# app/services/scraper.py

import httpx
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, quote, urljoin
from readability import Document

GOOGLE_NEWS = "https://news.google.com"


class Scraper:

    # ------------------------------------------------------------
    # 1) RSS Search (Fastest & Most Reliable)
    # ------------------------------------------------------------
    async def search_rss(self, keyword: str) -> list[str]:
        encoded = quote(keyword)

        rss_url = (
            f"https://news.google.com/rss/search?q={encoded}"
            f"&hl=en-IN&gl=IN&ceid=IN:en"
        )

        feed = feedparser.parse(rss_url)
        urls = []

        for entry in feed.entries:

            # Best source — real publisher link
            if "feedburner_origlink" in entry:
                urls.append(entry.feedburner_origlink)
                continue

            # GUID sometimes contains the real link
            if getattr(entry, "guid", "").startswith("http"):
                urls.append(entry.guid)
                continue

            # Source link
            if hasattr(entry, "source") and hasattr(entry.source, "href"):
                urls.append(entry.source.href)
                continue

            # Default Google redirect link
            if hasattr(entry, "link"):
                urls.append(entry.link)
                continue

            # Very rare fallback
            try:
                urls.append(entry.links[0]["href"])
            except:
                pass

        # Remove duplicates
        return list(dict.fromkeys(urls))

    # ------------------------------------------------------------
    # 2) HTML Search (when RSS returns empty)
    # ------------------------------------------------------------
    async def search_html(self, keyword: str) -> list[str]:

        search_url = (
            f"{GOOGLE_NEWS}/search?q={quote(keyword)}"
            f"&hl=en-IN&gl=IN&ceid=IN:en"
        )

        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            timeout=20
        ) as client:
            r = await client.get(search_url)

        soup = BeautifulSoup(r.text, "lxml")

        selectors = [
            "article h3 a",
            "h3 a",
            "a.WwrzSb",
            "a.ipQwMb",
            "a.VDXfz",
        ]

        urls = []

        for sel in selectors:
            for a in soup.select(sel):
                link = a.get("href")
                if not link:
                    continue

                # Convert ./article/... to absolute
                if link.startswith("./"):
                    full = urljoin(GOOGLE_NEWS, link[2:])
                else:
                    full = urljoin(GOOGLE_NEWS, link)

                urls.append(full)

        return list(dict.fromkeys(urls))

    # ------------------------------------------------------------
    # 3) Extract real URL from Google redirect
    # ------------------------------------------------------------
    def extract_real_url(self, url: str) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        # https://news.google.com/... ?url=https://actual.com
        if "url" in query:
            return query["url"][0]

        return url

    # ------------------------------------------------------------
    # 4) Scrape Real Article Content
    # ------------------------------------------------------------
    async def scrape_article(self, url: str) -> dict:

        real_url = self.extract_real_url(url)

        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
            timeout=20
        ) as client:
            r = await client.get(real_url)

        html = r.text

        try:
            doc = Document(html)
        except:
            raise Exception("Readability failed")

        title = doc.title() or "Untitled Article"
        summary_html = doc.summary()

        soup = BeautifulSoup(summary_html, "lxml")
        clean_text = soup.get_text(" ", strip=True)

        sentences = clean_text.split(". ")
        snippet = ". ".join(sentences[:2]).strip() + "."

        return {
            "url": real_url,
            "title": title[:500],
            "summary": clean_text[:5000],
            "snippet": snippet[:500],
            "raw_html": html
        }

    # ------------------------------------------------------------
    # 5) Combined Search: RSS first → HTML fallback
    # ------------------------------------------------------------
    async def search_and_scrape(self, keyword: str) -> list[dict]:

        # Step 1 — Try RSS (best)
        urls = await self.search_rss(keyword)

        # Step 2 — Fallback to HTML (if RSS fails)
        if not urls:
            print("⚠️ RSS returned zero results → using HTML fallback")
            urls = await self.search_html(keyword)

        articles = []

        for url in urls[:5]:
        # ------------------------------------------------
        # STEP 1 — Check if article already exists in DB
        # ------------------------------------------------
            try:
                existing = await db.fetch_by_query("articles", f"url=eq.{url}")
                if existing:
                    # already saved earlier → skip scraping
                    # OPTIONAL: remove log noise
                    # print("Skipping existing URL:", url)
                    continue
            except Exception:
                pass  # if DB check fails, still try scraping

            # ------------------------------------------------
            # STEP 2 — Scrape if not already in DB
            # ------------------------------------------------
            try:
                data = await self.scrape_article(url)
                articles.append(data)
            except Exception as e:
                print("Error scraping:", url, e)

        return articles

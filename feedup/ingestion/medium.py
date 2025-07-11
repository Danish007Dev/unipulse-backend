import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_ingestor import BaseIngestor

MEDIUM_RSS_FEEDS = {
    "flutter": "https://medium.com/feed/tag/flutter",
    "ai": "https://medium.com/feed/tag/artificial-intelligence",
    "tools": "https://medium.com/feed/tag/tools",
    "programming": "https://medium.com/feed/tag/programming",
}

DEPARTMENT_TAGS = {
    "Computer Science": ["flutter", "ai", "tools", "programming", "cloud", "linux"],
}

def assign_department(tags):
    tags = [tag.lower() for tag in tags]
    for dept, keywords in DEPARTMENT_TAGS.items():
        if any(tag in keywords for tag in tags):
            return dept
    return "Computer Science"

def extract_full_content(url, fallback_summary=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")  # use "html.parser" if lxml not available
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            if text and len(text.split()) > 100:  # must be meaningful
                return text
    except Exception as e:
        print(f"[Medium] Primary fetch failed for {url}: {e}")

    # Retry once with increased timeout
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            if text and len(text.split()) > 100:
                return text
    except Exception as e:
        print(f"[Medium] Retry fetch failed for {url}: {e}")

    print(f"[Medium] ❌ Failed to extract full article from {url}, using summary fallback.")
    return fallback_summary or ""

class MediumIngestor(BaseIngestor):
    def fetch_articles(self):
        articles = []
        for tag, rss_url in MEDIUM_RSS_FEEDS.items():
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]:
                full_content = extract_full_content(entry.link, fallback_summary=entry.summary)
                articles.append({
                    "title": entry.title,
                    "source_url": entry.link,
                    "source_name": "Medium",
                    "published_at": datetime(*entry.published_parsed[:6]),
                    "raw_content": full_content,
                    "tag_suggestions": [tag],
                    "department_name": assign_department([tag]),
                })
        return articles

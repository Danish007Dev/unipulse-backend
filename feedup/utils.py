# feedup/utils.py
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
MODEL = genai.GenerativeModel("models/gemini-2.5-flash")

SUMMARY_PROMPT_TEMPLATE = """
Summarize the following article into a small paragraph or points as suitable. Then suggest at least one or two interactive coding tips or critical thinking prompts related to the topic.

Article:
"""

def summarize_articles(article):
    content = article.raw_content.strip()
    if len(content.split()) < 100:
        return False, f"Skipped (too short: {len(content.split())} words)"

    prompt = SUMMARY_PROMPT_TEMPLATE + content
    try:
        response = MODEL.generate_content(prompt)
        text = response.text.strip()

        # Parse response
        summary_lines = []
        prompt_line = None

        for line in text.splitlines():
            line = line.strip("- *\n")
            if line.lower().startswith("try") or "prompt" in line.lower() or len(summary_lines) >= 3:
                prompt_line = line
                break
            if line:
                summary_lines.append(line)

        if not summary_lines:
            return False, "No summary returned"

        article.summary = "\n".join(summary_lines[:3])
        article.prompts = [prompt_line or "Explore this concept further."]
        article.ai_generated = True
        article.save()
        return True, None

    except Exception as e:
        return False, str(e)


# feedup/utils.py
from .models import ArticleStaging
from feedup.ingestion.devto import DevtoIngestor
from feedup.ingestion.medium import MediumIngestor
from django.utils.timezone import make_aware, is_naive
from datetime import datetime

def ingest_articles(tags=None):
    tags = tags or ["flutter", "ai", "tools", "programming"]
    devto = DevtoIngestor(tags)
    medium = MediumIngestor(tags)

    articles = devto.fetch_articles() + medium.fetch_articles()
    saved_count = 0
    errors = []

    for art in articles:
        try:
            published_at = art["published_at"]
            if isinstance(published_at, datetime) and is_naive(published_at):
                published_at = make_aware(published_at)

            obj, created = ArticleStaging.objects.get_or_create(
                source_url=art["source_url"],
                defaults={
                    "title": art["title"],
                    "source_name": art["source_name"],
                    "raw_content": art["raw_content"],
                    "tag_suggestions": art["tag_suggestions"],
                    "published_at": published_at,
                }
            )
            if created:
                saved_count += 1
        except Exception as e:
            errors.append(f"{art.get('title', 'Unknown')} → {str(e)}")

    return saved_count, errors

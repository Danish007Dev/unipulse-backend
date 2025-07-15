import json
import google.generativeai as genai
import os
from .models import Article

# Configure the Gemini API client
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    MODEL = genai.GenerativeModel('models/gemini-2.5-flash')
except Exception as e:
    print(f"Could not configure Gemini API: {e}")
    MODEL = None

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


def generate_questions_for_article(article: Article) -> list:
    """
    Generates a list of initial questions for an article using the Gemini API.
    """
    if not MODEL:
        raise Exception("Gemini API not configured")

    prompt = f"""
    Based on the following article title and summary, generate three distinct, short, and engaging follow-up questions a curious reader might ask.
    Return the questions as a JSON list of strings. For example: ["Question 1?", "Question 2?", "Question 3?"].

    Title: "{article.title}"
    Summary: "{article.summary}"

    JSON List of Questions:
    """
    try:
        response = MODEL.generate_content(prompt)
        # Basic cleaning to extract the JSON list
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error generating questions from Gemini: {e}")
        # Fallback questions
        return [
            f"What is the main idea of '{article.title}'?",
            "What are the key takeaways from this article?",
            "Can you explain the core concepts to a beginner?",
        ]


def get_ai_response(article: Article, query: str) -> str:
    """
    Generates an answer to a user's query based on the article's content.
    """
    if not MODEL:
        raise Exception("Gemini API not configured")

    prompt = f"""
    You are an AI assistant that explains technical topics in under 100 words based only on the provided article title and summary.
    Stay focused on the core idea of the article. Do not go beyond its scope. Use external resources or search only if it helps explain the core logic more clearly.


    Article Title: "{article.title}"
    Article Summary: "{article.summary}"

    ---
    User's Question: "{query}"
    ---

    Answer:
    """
    try:
        response = MODEL.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error getting answer from Gemini: {e}")
        return "I'm sorry, I encountered an error while trying to answer your question. Please try again."


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

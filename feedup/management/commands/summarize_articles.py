# inside summarize_articles.py
from django.core.management.base import BaseCommand
from feedup.models import ArticleStaging
from feedup.utils import summarize_article

class Command(BaseCommand):
    help = "Use Gemini to summarize approved tech articles"

    def handle(self, *args, **kwargs):
        articles = ArticleStaging.objects.filter(approved=True, ai_generated=False)
        count = 0
        for article in articles:
            success, error = summarize_article(article)
            if success:
                count += 1
            else:
                self.stderr.write(f"❌ {article.title} — {error}")

        self.stdout.write(self.style.SUCCESS(f"✅ AI summarized {count} articles."))

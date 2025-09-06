from django.core.management.base import BaseCommand
from feedup.utils import ingest_articles

class Command(BaseCommand):
    help = "Fetch tech articles from Dev.to and Medium and save them."

    def handle(self, *args, **kwargs):
        count, errors = ingest_articles()

        self.stdout.write(self.style.SUCCESS(f"✅ Imported {count} new articles."))
        if errors:
            self.stderr.write(f"❌ {len(errors)} errors occurred:")
            for e in errors[:5]:  # show only first few errors
                self.stderr.write(f" - {e}")

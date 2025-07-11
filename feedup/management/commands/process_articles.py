from django.core.management.base import BaseCommand
from django.db import transaction
from feedup.models import ArticleStaging, Article

class Command(BaseCommand):
    help = 'Processes articles from the staging table and moves them to the final Article table.'

    def handle(self, *args, **options):
        # Find all articles in the staging table that have not been processed yet.
        staged_articles = ArticleStaging.objects.filter(processed=True)
        
        if not staged_articles.exists():
            self.stdout.write(self.style.SUCCESS('✅ No new articles to process.'))
            return

        self.stdout.write(f'Found {staged_articles.count()} articles to process...')

        processed_count = 0
        with transaction.atomic():
            for staged_article in staged_articles:
                try:
                    # Create a new article in the final table
                    # This assumes the fields have the same names. Adjust if necessary.
                    final_article = Article.objects.create(
                        title=staged_article.title,
                        source_url=staged_article.source_url,
                        source_name=staged_article.source_name,
                        summary=staged_article.summary, # Or generate a summary here
                        prompts=staged_article.prompts,
                        published_at=staged_article.published_at,
                        staging_article=staged_article # Link back to the staging entry
                    )
                    
                    # Mark the staged article as processed
                    staged_article.processed = True
                    staged_article.save()
                    
                    processed_count += 1
                    self.stdout.write(f'  -> Processed and created article: "{final_article.title[:50]}..."')

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error processing article {staged_article.id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Successfully processed {processed_count} articles.'))

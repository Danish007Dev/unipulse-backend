from django.core.management.base import BaseCommand
from django.db import transaction
from feedup.models import ArticleStaging, Article

class Command(BaseCommand):
    help = 'Process approved articles from staging to production'

    def handle(self, *args, **options):
        # Get all approved but not processed articles
        articles_to_process = ArticleStaging.objects.filter(
            approved=True, 
            processed=False
        )
        
        self.stdout.write(f"Found {articles_to_process.count()} articles to process...")
        
        success_count = 0
        
        # Process each article in its own transaction
        for staged_article in articles_to_process:
            try:
                with transaction.atomic():
                    # Check if article with this URL already exists
                    if Article.objects.filter(source_url=staged_article.source_url).exists():
                        self.stdout.write(self.style.WARNING(
                            f"Skipping article {staged_article.id}: Article with URL {staged_article.source_url} already exists."
                        ))
                        # Mark as processed anyway since we don't need to process it again
                        staged_article.processed = True
                        staged_article.save()
                        continue
                        
                    # Create the Article record
                    Article.objects.create(
                        title=staged_article.title,
                        source_url=staged_article.source_url,
                        source_name=staged_article.source_name,
                        summary=staged_article.summary,
                        prompts=staged_article.prompts,
                        published_at=staged_article.published_at,
                        staging_article=staged_article
                    )
                    
                    # Mark as processed
                    staged_article.processed = True
                    staged_article.save()
                    
                    success_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing article {staged_article.id}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"🎉 Successfully processed {success_count} articles."))

from django.core.management.base import BaseCommand
from feedup.ingestion.service import DataIngestionService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch computer science conferences and research updates from Google Scholar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--conferences-only',
            action='store_true',
            help='Fetch only conference data',
        )
        parser.add_argument(
            '--research-only',
            action='store_true',
            help='Fetch only research updates from Google Scholar',
        )
        parser.add_argument(
            '--max-papers',
            type=int,
            default=20,
            help='Maximum number of papers to fetch from Google Scholar (default: 20)',
        )

    def handle(self, *args, **options):
        max_papers = options['max_papers']
        service = DataIngestionService(max_papers=max_papers)
        
        conferences_only = options['conferences_only']
        research_only = options['research_only']
        
        if conferences_only and research_only:
            self.stderr.write(self.style.ERROR(
                "Error: Cannot use both --conferences-only and --research-only together."
            ))
            return
        
        if conferences_only:
            self.stdout.write("Fetching conference data...")
            conferences_added = service.fetch_and_store_conferences()
            self.stdout.write(self.style.SUCCESS(
                f"✅ Successfully added {conferences_added} new conferences."
            ))
            
        elif research_only:
            self.stdout.write(f"Fetching research updates from Google Scholar (max: {max_papers})...")
            research_added = service.fetch_and_store_research()
            self.stdout.write(self.style.SUCCESS(
                f"✅ Successfully added {research_added} new research updates from Google Scholar."
            ))
            
        else:
            # Fetch both by default
            self.stdout.write(f"Fetching both conference and research data (max papers: {max_papers})...")
            result = service.fetch_all_data()
            self.stdout.write(self.style.SUCCESS(
                f"✅ Successfully added {result['conferences_added']} new conferences and "
                f"{result['research_added']} new research updates from Google Scholar."
            ))
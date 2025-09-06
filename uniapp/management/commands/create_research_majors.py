# Create a management command: management/commands/create_research_majors.py
from django.core.management.base import BaseCommand
from uniapp.models import ResearchMajor

class Command(BaseCommand):
    help = 'Create standard research majors'

    def handle(self, *args, **options):
        # Clear existing
        ResearchMajor.objects.all().delete()
        self.stdout.write("Cleared existing majors")
        
        # Create fresh majors
        majors_data = [
            ('Machine Learning & AI', 'Machine Learning & AI', 'AI, ML, Neural Networks, Deep Learning'),
            ('Software Engineering', 'Software Engineering', 'Software Development, Testing, DevOps'),
            ('Systems & Networks', 'Systems & Networks', 'Distributed Systems, Cloud Computing, Networks'),
            ('Cybersecurity', 'Cybersecurity', 'Network Security, Cryptography, Privacy'),
            ('Human-Computer Interaction', 'Human-Computer Interaction', 'UX/UI, VR/AR, Accessibility'),
            ('Data Science & Analytics', 'Data Science & Analytics', 'Big Data, Analytics, Data Mining'),
            ('Emerging Technologies', 'Emerging Technologies', 'Quantum Computing, IoT, Blockchain'),
        ]
        
        created = 0
        for name, category, description in majors_data:
            major, was_created = ResearchMajor.objects.get_or_create(
                category=category,
                defaults={'name': name, 'description': description}
            )
            if was_created:
                created += 1
                self.stdout.write(f"Created: {name}")
            else:
                self.stdout.write(f"Already exists: {name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Created {created} new research majors")
        )
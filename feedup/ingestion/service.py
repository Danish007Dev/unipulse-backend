import logging
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
import datetime
import hashlib

from ..models import Conference, ResearchUpdate

# Import fetchers with error handling
try:
    from .research_fetchers import GoogleScholarFetcher, SimpleGoogleScholarFetcher
    RESEARCH_FETCHERS_AVAILABLE = True
except ImportError as e:
    RESEARCH_FETCHERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"Research fetchers not available: {e}")

logger = logging.getLogger(__name__)

class DataIngestionService:
    """Service to fetch and store conference and research data."""
    
    def __init__(self, max_papers: int = 20):
        self.max_papers = max_papers
        
        # Initialize research fetchers with fallback
        self.research_fetchers = []
        
        if RESEARCH_FETCHERS_AVAILABLE:
            try:
                # Try to use Google Scholar fetcher first
                self.research_fetchers.append(GoogleScholarFetcher(max_papers=max_papers))
            except Exception as e:
                logger.warning(f"Could not initialize GoogleScholarFetcher: {e}")
                try:
                    # Fallback to simple fetcher
                    self.research_fetchers.append(SimpleGoogleScholarFetcher(max_papers=max_papers))
                except Exception as e2:
                    logger.error(f"Could not initialize any research fetcher: {e2}")
        
        if not self.research_fetchers:
            logger.warning("No research fetchers available, will use mock data")
    
    def fetch_and_store_research(self) -> int:
        """Fetch and store research updates."""
        total_added = 0
        
        if not self.research_fetchers:
            # Create mock data if no fetchers available
            mock_data = self._get_fallback_mock_data()
            total_added = self._store_research_data(mock_data)
            logger.info(f"Added {total_added} mock research items (no fetchers available)")
            return total_added
        
        for fetcher in self.research_fetchers:
            try:
                logger.info(f"Fetching research from {fetcher.source_name}")
                research_data = fetcher.fetch()
                
                if research_data:
                    added = self._store_research_data(research_data)
                    total_added += added
                    logger.info(f"Added {added} new research items from {fetcher.source_name}")
                    break  # Use first successful fetcher
                else:
                    logger.warning(f"No data returned from {fetcher.source_name}")
                    
            except Exception as e:
                logger.error(f"Error with fetcher {fetcher.source_name}: {str(e)}")
                continue
        
        # If no fetchers worked, use fallback mock data
        if total_added == 0:
            logger.warning("All fetchers failed, using fallback mock data")
            mock_data = self._get_fallback_mock_data()
            total_added = self._store_research_data(mock_data)
        
        logger.info(f"Research ingestion complete. Added {total_added} new items.")
        return total_added
    
    def _store_research_data(self, research_data: List[Dict[str, Any]]) -> int:
        """Store research data in database."""
        total_added = 0
        
        for item in research_data:
            try:
                # Check if already exists
                if not ResearchUpdate.objects.filter(unique_hash=item['unique_hash']).exists():
                    ResearchUpdate.objects.create(**item)
                    total_added += 1
                    logger.debug(f"Added research: {item['title']}")
                else:
                    logger.debug(f"Research already exists: {item['title']}")
            
            except Exception as e:
                logger.error(f"Error saving research item '{item.get('title', 'Unknown')}': {str(e)}")
                continue
        
        return total_added
    
    def _get_fallback_mock_data(self) -> List[Dict[str, Any]]:
        """Generate fallback mock data when no fetchers are available."""
        
        def generate_hash(content: str) -> str:
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        
        mock_papers = [
            {
                'title': 'Advances in Machine Learning for Natural Language Processing',
                'summary': 'This comprehensive survey examines recent developments in machine learning techniques applied to natural language processing. We cover transformer architectures, attention mechanisms, and their applications in machine translation, sentiment analysis, and text generation. The paper also discusses emerging trends like few-shot learning and transfer learning in NLP contexts.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=15),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_001',
                'authors': 'Zhang, L., Wang, M., Chen, Y., Rodriguez, A.',
                'institution': 'Stanford University',
                'category': 'Natural Language Processing',
                'unique_hash': generate_hash(f"fallback_paper_1_{datetime.date.today()}")
            },
            {
                'title': 'Distributed Systems Architecture for Cloud-Native Applications',
                'summary': 'An in-depth analysis of distributed systems patterns and their implementation in modern cloud-native applications. This work covers microservices architecture, containerization with Docker and Kubernetes, service mesh technologies, and distributed data management strategies. We present case studies from major tech companies and provide practical guidelines for system architects.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=30),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_002',
                'authors': 'Davis, M., Wilson, R., Garcia, L., Thompson, K.',
                'institution': 'MIT',
                'category': 'Distributed Systems',
                'unique_hash': generate_hash(f"fallback_paper_2_{datetime.date.today()}")
            },
            {
                'title': 'Computer Vision Applications in Autonomous Vehicle Navigation',
                'summary': 'This paper explores the latest computer vision techniques used in autonomous vehicle systems. We examine real-time object detection algorithms, depth estimation methods, semantic segmentation for road understanding, and sensor fusion approaches. The work includes extensive testing on various datasets and real-world scenarios.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=45),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_003',
                'authors': 'Johnson, P., Lee, H., Kumar, S., Brown, T.',
                'institution': 'Carnegie Mellon University',
                'category': 'Computer Vision',
                'unique_hash': generate_hash(f"fallback_paper_3_{datetime.date.today()}")
            },
            {
                'title': 'Cybersecurity in IoT Networks: Threats and Countermeasures',
                'summary': 'A comprehensive study of cybersecurity challenges in Internet of Things networks. We analyze common attack vectors including DDoS, man-in-the-middle attacks, and device hijacking. The paper presents novel detection algorithms using machine learning and proposes a multi-layered security framework for IoT deployments.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=60),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_004',
                'authors': 'Miller, J., Anderson, P., Taylor, K., White, M.',
                'institution': 'Georgia Institute of Technology',
                'category': 'Cybersecurity',
                'unique_hash': generate_hash(f"fallback_paper_4_{datetime.date.today()}")
            },
            {
                'title': 'Software Engineering Practices for Large-Scale AI Systems',
                'summary': 'This study investigates software engineering best practices for developing and maintaining large-scale artificial intelligence systems. We examine code organization, testing strategies for ML models, continuous integration/deployment for AI applications, and monitoring techniques for production ML systems.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=20),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_005',
                'authors': 'Smith, D., Kim, Y., Patel, N., Jones, R.',
                'institution': 'University of California Berkeley',
                'category': 'Software Engineering',
                'unique_hash': generate_hash(f"fallback_paper_5_{datetime.date.today()}")
            },
            {
                'title': 'Data Science Approaches for Climate Change Modeling',
                'summary': 'We present novel data science methodologies for climate change prediction and analysis. This work combines big data analytics, machine learning algorithms, and statistical modeling to process climate datasets. The paper includes case studies on temperature prediction, weather pattern analysis, and environmental impact assessment.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=35),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_006',
                'authors': 'Green, A., Blue, B., Ocean, C., Forest, D.',
                'institution': 'Harvard University',
                'category': 'Data Science',
                'unique_hash': generate_hash(f"fallback_paper_6_{datetime.date.today()}")
            },
            {
                'title': 'Human-Computer Interaction in Virtual Reality Environments',
                'summary': 'An exploration of user interface design principles and interaction paradigms in virtual reality systems. We study gesture recognition, haptic feedback, eye tracking, and voice commands in VR contexts. The research includes usability studies and guidelines for creating intuitive VR experiences.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=50),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_007',
                'authors': 'Virtual, V., Reality, R., Interface, I., Design, D.',
                'institution': 'University of Washington',
                'category': 'Human-Computer Interaction',
                'unique_hash': generate_hash(f"fallback_paper_7_{datetime.date.today()}")
            },
            {
                'title': 'Advanced Algorithms for Graph Neural Networks',
                'summary': 'This paper presents new algorithmic approaches for training and optimizing graph neural networks. We introduce efficient algorithms for large-scale graph processing, novel attention mechanisms for graph structures, and techniques for handling dynamic graphs. Experimental results show significant improvements in performance and scalability.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=25),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_008',
                'authors': 'Graph, G., Network, N., Algorithm, A., Neural, N.',
                'institution': 'Princeton University',
                'category': 'Algorithms',
                'unique_hash': generate_hash(f"fallback_paper_8_{datetime.date.today()}")
            },
            {
                'title': 'Database Systems for Real-Time Analytics',
                'summary': 'We examine modern database architectures designed for real-time analytics workloads. This work covers column-store databases, in-memory computing, distributed query processing, and stream processing systems. The paper includes performance benchmarks and recommendations for selecting appropriate database technologies.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=40),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_009',
                'authors': 'Database, D., Analytics, A., Stream, S., Processing, P.',
                'institution': 'University of Illinois',
                'category': 'Database Systems',
                'unique_hash': generate_hash(f"fallback_paper_9_{datetime.date.today()}")
            },
            {
                'title': 'Quantum Computing Applications in Cryptography',
                'summary': 'An investigation of quantum computing impacts on modern cryptographic systems. We analyze quantum algorithms for breaking traditional encryption methods and explore post-quantum cryptography solutions. The paper discusses practical implications for cybersecurity and provides recommendations for transitioning to quantum-resistant encryption.',
                'publication_date': datetime.date.today() - datetime.timedelta(days=55),
                'url': 'https://scholar.google.com',
                'source': 'fallback_mock',
                'source_id': 'fallback_010',
                'authors': 'Quantum, Q., Crypto, C., Security, S., Future, F.',
                'institution': 'Caltech',
                'category': 'Cybersecurity',
                'unique_hash': generate_hash(f"fallback_paper_10_{datetime.date.today()}")
            }
        ]
        
        return mock_papers[:self.max_papers]
    
    def fetch_and_store_conferences(self) -> int:
        """Fetch conferences - placeholder for now."""
        logger.info("Conference fetching not implemented yet")
        return 0
    
    def fetch_all_data(self) -> Dict[str, int]:
        """Fetch research updates only (since conferences aren't implemented yet)."""
        research_added = self.fetch_and_store_research()
        
        return {
            'conferences_added': 0,  # Placeholder
            'research_added': research_added,
            'timestamp': timezone.now()
        }
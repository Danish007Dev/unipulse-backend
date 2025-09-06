import re
import datetime
import time
import random
import logging
import threading
import platform
from typing import List, Dict, Any, Optional, Tuple
import hashlib

from .base_ingestor import BaseFetcher

logger = logging.getLogger(__name__)

class TimeoutException(Exception):
    pass

class CrossPlatformTimeout:
    """Cross-platform timeout handler that works on both Windows and Unix."""
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.timer = None
        self.timed_out = False
    
    def __enter__(self):
        def timeout_handler():
            self.timed_out = True
            logger.warning(f"Operation timed out after {self.timeout_seconds} seconds")
        
        self.timer = threading.Timer(self.timeout_seconds, timeout_handler)
        self.timer.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        
        if self.timed_out:
            raise TimeoutException(f"Operation timed out after {self.timeout_seconds} seconds")

class SmartSearchManager:
    """Manages diverse search terms with intelligent rotation and categorization."""
    
    def __init__(self):
        # Categorized search terms with different approaches
        self.search_categories = {
            'Machine Learning & AI': [
                'machine learning algorithms 2024',
                'deep learning neural networks',
                'artificial intelligence applications',
                'reinforcement learning systems',
                'generative AI models',
                'transformer architectures',
                'computer vision deep learning',
                'natural language processing transformers',
            ],
            'Software Engineering': [
                'software engineering practices 2024',
                'DevOps continuous integration',
                'microservices architecture',
                'software testing methodologies',
                'code quality analysis',
                'agile software development',
                'software design patterns',
                'programming languages comparison',
            ],
            'Systems & Networks': [
                'distributed systems design',
                'cloud computing architecture',
                'network security protocols',
                'database systems performance',
                'operating systems research',
                'blockchain technology applications',
                'edge computing frameworks',
                'container orchestration',
            ],
            'Cybersecurity': [
                'cybersecurity threat detection',
                'cryptography algorithms',
                'network intrusion detection',
                'privacy preserving techniques',
                'security vulnerability analysis',
                'zero trust architecture',
                'IoT security frameworks',
                'quantum cryptography',
            ],
            'Human-Computer Interaction': [
                'user experience design',
                'human computer interaction',
                'virtual reality interfaces',
                'augmented reality applications',
                'accessibility technology',
                'mobile user interfaces',
                'conversational AI interfaces',
                'gesture recognition systems',
            ],
            'Data Science & Analytics': [
                'big data analytics',
                'data mining techniques',
                'statistical learning methods',
                'data visualization methods',
                'time series analysis',
                'recommender systems',
                'knowledge discovery databases',
                'predictive analytics models',
            ],
            'Emerging Technologies': [
                'quantum computing algorithms',
                'Internet of Things platforms',
                'autonomous vehicle systems',
                'robotic process automation',
                'digital twin technology',
                'neuromorphic computing',
                'biometric authentication',
                'smart city technologies',
            ]
        }
        
        # Track usage to ensure diversity
        self.category_usage = {category: 0 for category in self.search_categories}
        self.term_usage = {}
        
    def get_diverse_search_terms(self, max_terms: int = 8) -> List[Tuple[str, str]]:
        """Get diverse search terms with their categories."""
        selected_terms = []
        
        # Sort categories by least used
        sorted_categories = sorted(
            self.search_categories.keys(),
            key=lambda cat: self.category_usage[cat]
        )
        
        terms_per_category = max(1, max_terms // len(sorted_categories))
        
        for category in sorted_categories:
            if len(selected_terms) >= max_terms:
                break
                
            # Get terms from this category, prioritizing unused ones
            category_terms = self.search_categories[category]
            unused_terms = [term for term in category_terms if self.term_usage.get(term, 0) == 0]
            
            if unused_terms:
                # Use unused terms first
                terms_to_use = random.sample(unused_terms, min(terms_per_category, len(unused_terms)))
            else:
                # Fall back to least used terms
                sorted_terms = sorted(category_terms, key=lambda term: self.term_usage.get(term, 0))
                terms_to_use = sorted_terms[:terms_per_category]
            
            for term in terms_to_use:
                selected_terms.append((term, category))
                self.term_usage[term] = self.term_usage.get(term, 0) + 1
            
            self.category_usage[category] += len(terms_to_use)
        
        # Shuffle for randomness
        random.shuffle(selected_terms)
        return selected_terms[:max_terms]
    
    def get_time_based_searches(self) -> List[Tuple[str, str]]:
        """Get searches based on current trends and recent timeframes."""
        current_year = datetime.date.today().year
        
        time_based_terms = [
            (f"computer science research {current_year}", "Recent Research"),
            (f"artificial intelligence {current_year}", "Current AI"),
            (f"software engineering trends {current_year}", "Current SE"),
            ("machine learning applications recent", "Recent ML"),
            ("cybersecurity threats latest", "Current Security"),
            ("distributed systems modern", "Modern Systems"),
        ]
        
        return random.sample(time_based_terms, min(3, len(time_based_terms)))

class EnhancedGoogleScholarFetcher(BaseFetcher):
    """Enhanced fetcher with diverse search terms, smart categorization, and robust handling."""
    
    def __init__(self, max_papers: int = 20):
        super().__init__("enhanced_google_scholar")
        self.max_papers = max_papers
        self.is_windows = platform.system() == "Windows"
        self.search_manager = SmartSearchManager()
        
        # Performance tracking
        self.fetch_stats = {
            'total_attempts': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'papers_by_category': {},
        }
        
        # Check if scholarly is available
        try:
            from scholarly import scholarly
            self.scholarly = scholarly
            self.scholarly_available = True
            logger.info("Enhanced Google Scholar fetcher initialized with scholarly library")
        except ImportError:
            self.scholarly = None
            self.scholarly_available = False
            logger.warning("scholarly library not available")
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch diverse CS research papers using smart search strategy."""
        if not self.scholarly_available:
            logger.warning("Scholarly not available, returning enhanced mock data")
            return self.get_enhanced_mock_data()
        
        all_results = []
        self.fetch_stats['total_attempts'] += 1
        
        try:
            logger.info("Starting enhanced Google Scholar fetch with diverse search terms...")
            
            # Get diverse search terms
            search_terms = self.search_manager.get_diverse_search_terms(max_terms=6)
            
            # Add some time-based searches
            time_based_terms = self.search_manager.get_time_based_searches()
            search_terms.extend(time_based_terms)
            
            logger.info(f"Using {len(search_terms)} diverse search terms across categories")
            
            # Calculate papers per term
            papers_per_term = max(1, self.max_papers // len(search_terms))
            
            with CrossPlatformTimeout(60):  # Longer timeout for multiple searches
                for i, (term, category) in enumerate(search_terms):
                    if len(all_results) >= self.max_papers:
                        break
                    
                    logger.info(f"Search {i+1}/{len(search_terms)}: '{term}' ({category})")
                    
                    try:
                        results = self._fetch_from_term(term, category, papers_per_term)
                        if results:
                            all_results.extend(results)
                            logger.info(f"  -> Found {len(results)} papers")  # Changed → to ->
                        else:
                            logger.info(f"  -> No papers found")  # Changed → to ->
                        
                        # Rate limiting between searches
                        if i < len(search_terms) - 1:
                            time.sleep(random.uniform(2, 4))
                            
                    except Exception as e:
                        logger.warning(f"Error with search term '{term}': {str(e)}")
                        continue
            
            if all_results:
                # Remove duplicates and apply smart filtering
                unique_results = self._smart_deduplication(all_results)
                final_results = self._apply_quality_filters(unique_results)[:self.max_papers]
                
                self.fetch_stats['successful_fetches'] += 1
                self._update_category_stats(final_results)
                
                logger.info(f"Successfully fetched {len(final_results)} diverse papers")
                return final_results
            else:
                logger.warning("No results from any search terms, using enhanced mock data")
                return self.get_enhanced_mock_data()
                
        except TimeoutException:
            logger.error("Enhanced fetch timed out, using mock data")
            self.fetch_stats['failed_fetches'] += 1
            return self.get_enhanced_mock_data()
        except Exception as e:
            logger.error(f"Error in enhanced fetch: {str(e)}, using mock data")
            self.fetch_stats['failed_fetches'] += 1
            return self.get_enhanced_mock_data()
    
    def _fetch_from_term(self, search_term: str, category: str, max_papers: int) -> List[Dict[str, Any]]:
        """Fetch papers from a specific search term."""
        results = []
        
        try:
            search_query = self.scholarly.search_pubs(search_term)
            
            count = 0
            for paper in search_query:
                if count >= max_papers:
                    break
                
                try:
                    result = self._process_paper_enhanced(paper, category)
                    if result and self._is_quality_paper(result):
                        results.append(result)
                        count += 1
                    
                    # Small delay between papers
                    time.sleep(random.uniform(0.5, 1.0))
                    
                except Exception as e:
                    logger.debug(f"Error processing individual paper: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Error fetching from term '{search_term}': {str(e)}")
            return []
    
    def _process_paper_enhanced(self, paper: Dict[str, Any], suggested_category: str) -> Optional[Dict[str, Any]]:
        """Enhanced paper processing with better data extraction."""
        try:
            bib = paper.get('bib', {})
            title = bib.get('title', '').strip()
            
            if not title or len(title) < 10:
                return None
            
            # Enhanced publication date handling
            pub_date = self._extract_publication_date(bib)
            
            # Enhanced author extraction
            authors_str = self._extract_authors(bib)
            
            # Enhanced URL extraction
            url = self._extract_best_url(paper)
            
            # Enhanced abstract extraction
            abstract = self._extract_abstract(bib, paper)
            
            # Smart category determination
            category = self._determine_category_smart(title, abstract, suggested_category)
            
            # Enhanced institution extraction
            institution = self._extract_institution_enhanced(authors_str, bib)
            
            # Generate source ID
            source_id = self._generate_source_id(paper, title)
            
            # Generate unique hash with more robust method
            unique_hash = self._generate_robust_hash(title, authors_str, pub_date)
            
            return {
                'title': title,
                'summary': abstract,
                'publication_date': pub_date,
                'url': url,
                'source': self.source_name,
                'source_id': source_id,
                'authors': authors_str,
                'institution': institution,
                'category': category,
                'unique_hash': unique_hash,
                'search_category': suggested_category,  # Track which search found this
            }
            
        except Exception as e:
            logger.debug(f"Error in enhanced paper processing: {str(e)}")
            return None
    
    def _extract_publication_date(self, bib: Dict[str, Any]) -> datetime.date:
        """Enhanced publication date extraction."""
        pub_year = bib.get('pub_year')
        
        if pub_year:
            try:
                year = int(pub_year)
                # Only accept recent papers (last 5 years)
                current_year = datetime.date.today().year
                if year > current_year or year < (current_year - 5):
                    return datetime.date.today()
                
                # Try to get month if available
                pub_date_str = bib.get('pub_date', '')
                if pub_date_str and len(pub_date_str) > 4:
                    try:
                        return datetime.datetime.strptime(pub_date_str[:10], '%Y-%m-%d').date()
                    except:
                        pass
                
                # Default to mid-year
                return datetime.date(year, 6, 15)
            except (ValueError, TypeError):
                pass
        
        return datetime.date.today()
    
    def _extract_authors(self, bib: Dict[str, Any]) -> str:
        """Enhanced author extraction."""
        authors = bib.get('author', [])
        
        if isinstance(authors, list):
            # Clean author names and limit to reasonable number
            clean_authors = []
            for author in authors[:4]:  # Max 4 authors
                if isinstance(author, str):
                    clean_author = re.sub(r'[^\w\s,.-]', '', author).strip()
                    if clean_author and len(clean_author) > 1:
                        clean_authors.append(clean_author)
            
            if clean_authors:
                result = ', '.join(clean_authors)
                if len(clean_authors) < len(authors):
                    result += ' et al.'
                return result
        elif isinstance(authors, str):
            clean_authors = re.sub(r'[^\w\s,.-]', '', authors).strip()
            return clean_authors[:200] if clean_authors else 'Unknown'
        
        return 'Unknown'
    
    def _extract_best_url(self, paper: Dict[str, Any]) -> str:
        """Extract the best available URL for the paper."""
        # Priority order for URLs
        url_fields = ['pub_url', 'eprint_url', 'url_scholarbib']
        
        for field in url_fields:
            url = paper.get(field, '')
            if url and url.startswith('http'):
                return url
        
        # Fallback to scholar search
        title = paper.get('bib', {}).get('title', '')
        if title:
            return f"https://scholar.google.com/scholar?q={title.replace(' ', '+')}"
        
        return "https://scholar.google.com"
    
    def _extract_abstract(self, bib: Dict[str, Any], paper: Dict[str, Any]) -> str:
        """Enhanced abstract extraction."""
        abstract = bib.get('abstract', '')
        
        if not abstract:
            # Try other fields
            abstract = paper.get('abstract', '') or bib.get('summary', '')
        
        if not abstract or len(abstract) < 50:
            # Generate a basic description from title and venue
            title = bib.get('title', '')
            venue = bib.get('venue', '')
            if title:
                abstract = f"Research paper on {title.lower()}"
                if venue:
                    abstract += f", published in {venue}"
                abstract += ". Full abstract not available."
            else:
                abstract = "Abstract not available"
        
        # Clean and limit length
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        if len(abstract) > 800:
            abstract = abstract[:797] + '...'
        
        return abstract
    
    def _determine_category_smart(self, title: str, abstract: str, suggested_category: str) -> str:
        """Smart category determination with multiple strategies."""
        text = f"{title} {abstract}".lower()
        
        # Enhanced category keywords with weights
        category_patterns = {
            'Machine Learning': {
                'keywords': ['machine learning', 'ml', 'neural network', 'deep learning', 'ai', 'artificial intelligence', 'classification', 'regression', 'clustering'],
                'weight': 1.0
            },
            'Computer Vision': {
                'keywords': ['computer vision', 'image', 'visual', 'opencv', 'cnn', 'convolutional', 'object detection', 'segmentation'],
                'weight': 1.0
            },
            'Natural Language Processing': {
                'keywords': ['nlp', 'natural language', 'text mining', 'language model', 'bert', 'gpt', 'transformer', 'sentiment'],
                'weight': 1.0
            },
            'Cybersecurity': {
                'keywords': ['security', 'cybersecurity', 'encryption', 'privacy', 'vulnerability', 'attack', 'cryptography', 'authentication'],
                'weight': 1.0
            },
            'Software Engineering': {
                'keywords': ['software', 'programming', 'development', 'code', 'testing', 'debugging', 'devops', 'agile'],
                'weight': 1.0
            },
            'Distributed Systems': {
                'keywords': ['distributed', 'cloud', 'microservices', 'scalability', 'cluster', 'parallel', 'concurrent'],
                'weight': 1.0
            },
            'Human-Computer Interaction': {
                'keywords': ['hci', 'user interface', 'usability', 'user experience', 'interaction', 'ui', 'ux'],
                'weight': 1.0
            },
            'Data Science': {
                'keywords': ['data science', 'big data', 'analytics', 'data mining', 'statistics', 'visualization'],
                'weight': 1.0
            },
            'Algorithms': {
                'keywords': ['algorithm', 'complexity', 'optimization', 'graph', 'sorting', 'computational'],
                'weight': 1.0
            }
        }
        
        # Calculate scores for each category
        category_scores = {}
        for category, pattern in category_patterns.items():
            score = 0
            for keyword in pattern['keywords']:
                if keyword in text:
                    score += pattern['weight']
            category_scores[category] = score
        
        # Get the highest scoring category
        if category_scores and max(category_scores.values()) > 0:
            best_category = max(category_scores, key=category_scores.get)
            return best_category
        
        # Fallback to suggested category or default
        if suggested_category and 'Recent' not in suggested_category and 'Current' not in suggested_category:
            return suggested_category
        
        return 'Computer Science'
    
    def _extract_institution_enhanced(self, authors: str, bib: Dict[str, Any]) -> str:
        """Enhanced institution extraction."""
        text = f"{authors} {bib.get('venue', '')}".lower()
        
        # Enhanced patterns for institution detection
        institution_patterns = [
            # Universities
            r'(\w+\s+university)',
            r'(university\s+of\s+[\w\s]+)',
            r'(\w+\s+institute\s+of\s+technology)',
            r'(\w+\s+college)',
            # Specific prestigious institutions
            r'(stanford|mit|harvard|berkeley|cmu|carnegie mellon|georgia tech|caltech)',
            # Companies
            r'(google|microsoft|facebook|meta|apple|amazon|ibm|nvidia|openai)',
            # Research institutions
            r'(\w+\s+research\s+lab)',
            r'(\w+\s+research\s+center)',
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text)
            if match:
                institution = match.group(1)
                # Clean and format
                institution = ' '.join(word.capitalize() for word in institution.split())
                
                # Handle special cases
                if 'mit' in institution.lower():
                    return 'MIT'
                elif 'cmu' in institution.lower() or 'carnegie mellon' in institution.lower():
                    return 'Carnegie Mellon University'
                elif 'berkeley' in institution.lower():
                    return 'UC Berkeley'
                
                return institution
        
        return 'Various Institutions'
    
    def _generate_source_id(self, paper: Dict[str, Any], title: str) -> str:
        """Generate a robust source ID."""
        # Try different ID fields
        id_fields = ['scholar_id', 'citedby_url', 'url_scholarbib']
        
        for field in id_fields:
            value = paper.get(field, '')
            if value:
                if 'cites=' in value:
                    return value.split('cites=')[-1]
                elif field == 'scholar_id':
                    return value
        
        # Generate from title hash
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
        return f'gs_{title_hash[:12]}'
    
    def _generate_robust_hash(self, title: str, authors: str, pub_date: datetime.date) -> str:
        """Generate a robust hash for deduplication."""
        # Normalize title for better duplicate detection
        normalized_title = re.sub(r'[^\w\s]', '', title.lower())
        normalized_title = ' '.join(normalized_title.split())
        
        # Create unique identifier
        unique_id = f"{normalized_title}|{pub_date}|{authors[:50]}"
        return hashlib.md5(unique_id.encode('utf-8')).hexdigest()
    
    def _is_quality_paper(self, paper: Dict[str, Any]) -> bool:
        """Check if a paper meets quality criteria."""
        title = paper.get('title', '')
        summary = paper.get('summary', '')
        
        # Basic quality checks
        if len(title) < 15:
            return False
        
        if len(summary) < 30:
            return False
        
        # Check for spam indicators
        spam_indicators = ['buy', 'cheap', 'free download', 'click here']
        text_check = f"{title} {summary}".lower()
        if any(indicator in text_check for indicator in spam_indicators):
            return False
        
        return True
    
    def _smart_deduplication(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Smart deduplication based on multiple criteria."""
        unique_papers = []
        seen_hashes = set()
        seen_titles = set()
        
        for paper in papers:
            # Check exact hash first
            paper_hash = paper.get('unique_hash')
            if paper_hash in seen_hashes:
                continue
            
            # Check title similarity
            title = paper.get('title', '').lower()
            normalized_title = re.sub(r'[^\w\s]', '', title)
            normalized_title = ' '.join(normalized_title.split())
            
            if normalized_title in seen_titles:
                continue
            
            # Add to unique set
            seen_hashes.add(paper_hash)
            seen_titles.add(normalized_title)
            unique_papers.append(paper)
        
        return unique_papers
    
    def _apply_quality_filters(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply quality filters and sort papers."""
        # Filter by quality
        quality_papers = [paper for paper in papers if self._is_quality_paper(paper)]
        
        # Sort by publication date (newest first) and category diversity
        def sort_key(paper):
            pub_date = paper.get('publication_date', datetime.date.min)
            category_bonus = 0.1 if paper.get('category') != 'Computer Science' else 0
            return (pub_date, category_bonus)
        
        quality_papers.sort(key=sort_key, reverse=True)
        
        return quality_papers
    
    def _update_category_stats(self, papers: List[Dict[str, Any]]) -> None:
        """Update statistics about fetched papers."""
        for paper in papers:
            category = paper.get('category', 'Unknown')
            self.fetch_stats['papers_by_category'][category] = \
                self.fetch_stats['papers_by_category'].get(category, 0) + 1
    
    def get_enhanced_mock_data(self) -> List[Dict[str, Any]]:
        """Return enhanced mock data with better diversity and realism."""
        current_date = datetime.date.today()
        
        enhanced_mock_papers = [
            {
                'title': 'Federated Learning for Privacy-Preserving Healthcare Analytics',
                'summary': 'This research addresses critical privacy concerns in healthcare data analytics by implementing federated learning approaches. We propose a novel framework that enables collaborative machine learning across multiple healthcare institutions while maintaining strict patient privacy. Our method demonstrates significant improvements in diagnostic accuracy while ensuring HIPAA compliance and data sovereignty.',
                'publication_date': current_date - datetime.timedelta(days=8),
                'url': 'https://scholar.google.com/scholar?q=federated+learning+healthcare',
                'source': self.source_name,
                'source_id': 'enhanced_mock_001',
                'authors': 'Chen, L., Rodriguez, M., Patel, S., Kim, J.',
                'institution': 'Stanford Medical School',
                'category': 'Machine Learning',
                'unique_hash': self.generate_hash(f"enhanced_mock_1_{current_date}"),
                'search_category': 'Machine Learning & AI'
            },
            {
                'title': 'Quantum-Resistant Cryptographic Protocols for IoT Networks',
                'summary': 'As quantum computing advances threaten current cryptographic standards, this paper presents novel quantum-resistant cryptographic protocols specifically designed for resource-constrained IoT devices. We introduce lightweight post-quantum algorithms that maintain security while operating efficiently on devices with limited computational power and battery life.',
                'publication_date': current_date - datetime.timedelta(days=22),
                'url': 'https://scholar.google.com/scholar?q=quantum+cryptography+iot',
                'source': self.source_name,
                'source_id': 'enhanced_mock_002',
                'authors': 'Quantum, A., Security, B., IoT, C., Network, D.',
                'institution': 'MIT CSAIL',
                'category': 'Cybersecurity',
                'unique_hash': self.generate_hash(f"enhanced_mock_2_{current_date}"),
                'search_category': 'Cybersecurity'
            },
            {
                'title': 'Real-Time Computer Vision for Autonomous Drone Navigation in Complex Environments',
                'summary': 'We present a comprehensive computer vision system for autonomous drone navigation in GPS-denied and visually complex environments. Our approach combines SLAM, semantic segmentation, and obstacle avoidance using lightweight deep learning models optimized for real-time processing on embedded hardware. Extensive testing in urban and natural environments validates our approach.',
                'publication_date': current_date - datetime.timedelta(days=15),
                'url': 'https://scholar.google.com/scholar?q=computer+vision+drone+navigation',
                'source': self.source_name,
                'source_id': 'enhanced_mock_003',
                'authors': 'Flight, F., Vision, V., Navigate, N., Autonomous, A.',
                'institution': 'Carnegie Mellon Robotics Institute',
                'category': 'Computer Vision',
                'unique_hash': self.generate_hash(f"enhanced_mock_3_{current_date}"),
                'search_category': 'Machine Learning & AI'
            },
            {
                'title': 'Microservices Architecture Patterns for Large-Scale E-commerce Platforms',
                'summary': 'This paper analyzes microservices architecture patterns specifically tailored for large-scale e-commerce platforms. We examine service decomposition strategies, data consistency patterns, and fault tolerance mechanisms. Our case study with a major e-commerce platform demonstrates 40% improvement in system reliability and 60% reduction in deployment time.',
                'publication_date': current_date - datetime.timedelta(days=35),
                'url': 'https://scholar.google.com/scholar?q=microservices+ecommerce+architecture',
                'source': self.source_name,
                'source_id': 'enhanced_mock_004',
                'authors': 'Micro, M., Service, S., Scale, S., Commerce, C.',
                'institution': 'Google Cloud Research',
                'category': 'Software Engineering',
                'unique_hash': self.generate_hash(f"enhanced_mock_4_{current_date}"),
                'search_category': 'Software Engineering'
            },
            {
                'title': 'Conversational AI for Accessibility: Design Principles and User Experience Guidelines',
                'summary': 'This research establishes comprehensive design principles for conversational AI systems that serve users with disabilities. We conducted extensive user studies with visually impaired, hearing impaired, and motor-impaired users to understand their unique needs. Our guidelines cover voice interface design, multi-modal interaction, and adaptive behavior patterns.',
                'publication_date': current_date - datetime.timedelta(days=28),
                'url': 'https://scholar.google.com/scholar?q=conversational+ai+accessibility',
                'source': self.source_name,
                'source_id': 'enhanced_mock_005',
                'authors': 'Access, A., Converse, C., Interface, I., Design, D.',
                'institution': 'University of Washington',
                'category': 'Human-Computer Interaction',
                'unique_hash': self.generate_hash(f"enhanced_mock_5_{current_date}"),
                'search_category': 'Human-Computer Interaction'
            },
            {
                'title': 'Graph Neural Networks for Social Media Misinformation Detection',
                'summary': 'We propose a novel graph neural network architecture for detecting misinformation in social media networks. Our approach models information propagation patterns, user credibility networks, and content features to identify false information. Evaluation on real-world datasets shows 89% accuracy in misinformation detection with minimal false positives.',
                'publication_date': current_date - datetime.timedelta(days=18),
                'url': 'https://scholar.google.com/scholar?q=graph+neural+networks+misinformation',
                'source': self.source_name,
                'source_id': 'enhanced_mock_006',
                'authors': 'Graph, G., Neural, N., Social, S., Media, M.',
                'institution': 'Facebook AI Research',
                'category': 'Machine Learning',
                'unique_hash': self.generate_hash(f"enhanced_mock_6_{current_date}"),
                'search_category': 'Machine Learning & AI'
            },
            {
                'title': 'Edge Computing Frameworks for Real-Time Industrial IoT Analytics',
                'summary': 'This work presents comprehensive edge computing frameworks designed for real-time analytics in industrial IoT environments. We address latency-critical applications such as predictive maintenance, quality control, and safety monitoring. Our distributed architecture reduces cloud dependency by 70% while maintaining sub-millisecond response times.',
                'publication_date': current_date - datetime.timedelta(days=42),
                'url': 'https://scholar.google.com/scholar?q=edge+computing+industrial+iot',
                'source': self.source_name,
                'source_id': 'enhanced_mock_007',
                'authors': 'Edge, E., Compute, C., Industrial, I., Analytics, A.',
                'institution': 'Georgia Institute of Technology',
                'category': 'Distributed Systems',
                'unique_hash': self.generate_hash(f"enhanced_mock_7_{current_date}"),
                'search_category': 'Systems & Networks'
            },
            {
                'title': 'Automated Code Review Using Large Language Models and Static Analysis',
                'summary': 'We combine large language models with traditional static analysis tools to create an automated code review system. Our approach identifies bugs, security vulnerabilities, and code quality issues while providing human-readable explanations. Testing on open-source repositories shows 85% accuracy in identifying real issues with 12% false positive rate.',
                'publication_date': current_date - datetime.timedelta(days=12),
                'url': 'https://scholar.google.com/scholar?q=automated+code+review+llm',
                'source': self.source_name,
                'source_id': 'enhanced_mock_008',
                'authors': 'Code, C., Review, R., Language, L., Model, M.',
                'institution': 'Microsoft Research',
                'category': 'Software Engineering',
                'unique_hash': self.generate_hash(f"enhanced_mock_8_{current_date}"),
                'search_category': 'Software Engineering'
            }
        ]
        
        return enhanced_mock_papers[:self.max_papers]

class SimpleGoogleScholarFetcher(BaseFetcher):
    """A simple fetcher that always returns mock data quickly."""
    
    def __init__(self, max_papers: int = 10):
        super().__init__("simple_google_scholar")
        self.max_papers = max_papers
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Return mock data immediately."""
        logger.info(f"SimpleGoogleScholarFetcher: Returning {self.max_papers} mock papers")
        time.sleep(0.5)  # Simulate brief processing time
        return self.get_mock_data()
    
    def get_mock_data(self) -> List[Dict[str, Any]]:
        """Return simple mock data for quick testing."""
        current_date = datetime.date.today()
        
        mock_papers = [
            {
                'title': 'Deep Learning for Autonomous Vehicle Perception in Adverse Weather',
                'summary': 'This research addresses the challenge of autonomous vehicle perception in adverse weather conditions such as rain, snow, and fog. We propose robust deep learning models that maintain high accuracy in object detection and lane recognition despite challenging visibility conditions.',
                'publication_date': current_date - datetime.timedelta(days=12),
                'url': 'https://scholar.google.com/scholar?q=deep+learning+autonomous+vehicles',
                'source': self.source_name,
                'source_id': 'simple_001',
                'authors': 'Auto, A., Vehicle, V., Deep, D., Weather, W.',
                'institution': 'Tesla AI Research',
                'category': 'Computer Vision',
                'unique_hash': self.generate_hash(f"simple_paper_1_{current_date}")
            },
            {
                'title': 'Blockchain-Based Supply Chain Transparency and Traceability',
                'summary': 'We explore blockchain technology applications in supply chain management, focusing on transparency and traceability. Our framework enables end-to-end tracking of products from manufacturing to delivery while ensuring data integrity and preventing counterfeiting.',
                'publication_date': current_date - datetime.timedelta(days=28),
                'url': 'https://scholar.google.com/scholar?q=blockchain+supply+chain',
                'source': self.source_name,
                'source_id': 'simple_002',
                'authors': 'Chain, C., Block, B., Supply, S., Trace, T.',
                'institution': 'IBM Research',
                'category': 'Distributed Systems',
                'unique_hash': self.generate_hash(f"simple_paper_2_{current_date}")
            }
        ]
        
        return mock_papers[:self.max_papers]

# For backward compatibility, alias the enhanced fetcher
GoogleScholarFetcher = EnhancedGoogleScholarFetcher
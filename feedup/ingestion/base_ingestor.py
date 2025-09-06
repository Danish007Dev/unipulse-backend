import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib

class BaseIngestor(ABC):
    def __init__(self, tags):
        self.tags = tags

    @abstractmethod
    def fetch_articles(self):
        """Return a list of dicts with article info."""
        pass


logger = logging.getLogger(__name__)

class BaseFetcher(ABC):
    """Base class for all data fetchers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = self._create_robust_session()
    
    def _create_robust_session(self) -> requests.Session:
        """Create a requests session with retry logic and timeouts."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch data from the source and return a list of dictionaries."""
        pass
    
    def generate_hash(self, content: str) -> str:
        """Generate a unique hash for content deduplication."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def process_item(self, item: Any) -> Dict[str, Any]:
        """Process a single item. Can be overridden by subclasses."""
        # Default implementation - subclasses can override if needed
        return item
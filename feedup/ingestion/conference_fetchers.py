import re
import datetime
import feedparser
import logging
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from .base_ingestor import BaseFetcher
from ..models import Conference

logger = logging.getLogger(__name__)

class WikiCFPFetcher(BaseFetcher):
    """Fetcher for WikiCFP RSS feed."""
    
    def __init__(self):
        super().__init__("wikicfp")
        self.rss_url = "http://www.wikicfp.com/cfp/rss?cat=computer%20science"
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch conference data from WikiCFP RSS feed."""
        try:
            feed = feedparser.parse(self.rss_url)
            results = []
            
            for entry in feed.entries:
                processed_item = self.process_item(entry)
                if processed_item:
                    results.append(processed_item)
            
            logger.info(f"Fetched {len(results)} conferences from WikiCFP")
            return results
        except Exception as e:
            logger.error(f"Error fetching WikiCFP data: {str(e)}")
            return []
    
    def process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a WikiCFP RSS entry."""
        try:
            title = self.clean_text(item.get('title', ''))
            if not title:
                return None
                
            # Extract dates and location from description
            description = item.get('description', '')
            soup = BeautifulSoup(description, 'html.parser')
            description_text = soup.get_text()
            
            # Extract dates using regex
            date_pattern = r'When\s*:(.*?)Where\s*:'
            location_pattern = r'Where\s*:(.*?)Submission Deadline\s*:'
            deadline_pattern = r'Submission Deadline\s*:(.*?)$'
            
            date_match = re.search(date_pattern, description_text, re.DOTALL)
            location_match = re.search(location_pattern, description_text, re.DOTALL)
            deadline_match = re.search(deadline_pattern, description_text, re.DOTALL)
            
            date_str = date_match.group(1).strip() if date_match else ''
            location = location_match.group(1).strip() if location_match else 'Unknown'
            deadline = deadline_match.group(1).strip() if deadline_match else None
            
            # Parse date string
            try:
                # Handle various date formats
                if ' - ' in date_str:
                    start_str, end_str = date_str.split(' - ')
                    start_date = datetime.datetime.strptime(start_str.strip(), '%b %d, %Y').date()
                    end_date = datetime.datetime.strptime(end_str.strip(), '%b %d, %Y').date()
                else:
                    start_date = datetime.datetime.strptime(date_str.strip(), '%b %d, %Y').date()
                    end_date = start_date + datetime.timedelta(days=3)  # Default to 3-day conference
            except Exception:
                # Fallback to current date + 3 months if parsing fails
                start_date = datetime.date.today() + datetime.timedelta(days=90)
                end_date = start_date + datetime.timedelta(days=3)
            
            # Parse deadline
            deadline_date = None
            if deadline:
                try:
                    deadline_date = datetime.datetime.strptime(deadline.strip(), '%b %d, %Y').date()
                except Exception:
                    pass
                    
            # Generate unique identifier
            unique_id = f"{title}|{start_date}|{location}"
            unique_hash = self.generate_hash(unique_id)
            
            return {
                'title': title,
                'description': description_text,
                'start_date': start_date,
                'end_date': end_date,
                'location': location,
                'website_url': item.get('link', ''),
                'source': self.source_name,
                'source_id': item.get('id', ''),
                'deadline_submission': deadline_date,
                'unique_hash': unique_hash,
                'topics': 'Computer Science'
            }
        except Exception as e:
            logger.error(f"Error processing WikiCFP item: {str(e)}")
            return None


class ConferenceOrgFetcher(BaseFetcher):
    """Fetcher for AllConferences.org website."""
    
    def __init__(self):
        super().__init__("conferenceorg")
        self.url = "https://allconferences.com/search/searchResults.php?searchWord=computer+science&categoryId=&countryId=&stateId=&month=&format=json"
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch conference data from AllConferences.org."""
        try:
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('conferences', []):
                processed_item = self.process_item(item)
                if processed_item:
                    results.append(processed_item)
            
            logger.info(f"Fetched {len(results)} conferences from AllConferences.org")
            return results
        except Exception as e:
            logger.error(f"Error fetching AllConferences.org data: {str(e)}")
            return []
    
    def process_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an AllConferences.org item."""
        try:
            title = self.clean_text(item.get('title', ''))
            if not title:
                return None
                
            # Parse dates
            try:
                start_date_str = item.get('startDate', '')
                end_date_str = item.get('endDate', '')
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date
            except Exception:
                # Fallback dates
                start_date = datetime.date.today() + datetime.timedelta(days=90)
                end_date = start_date + datetime.timedelta(days=2)
            
            location = f"{item.get('city', '')}, {item.get('country', '')}"
            location = location.strip(', ')
            if not location:
                location = "Unknown"
            
            # Generate unique identifier
            unique_id = f"{title}|{start_date}|{location}"
            unique_hash = self.generate_hash(unique_id)
            
            return {
                'title': title,
                'description': item.get('description', ''),
                'start_date': start_date,
                'end_date': end_date,
                'location': location,
                'website_url': item.get('url', ''),
                'source': self.source_name,
                'source_id': item.get('id', ''),
                'unique_hash': unique_hash,
                'topics': item.get('keywords', '')
            }
        except Exception as e:
            logger.error(f"Error processing AllConferences.org item: {str(e)}")
            return None
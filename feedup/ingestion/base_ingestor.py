from abc import ABC, abstractmethod

class BaseIngestor(ABC):
    def __init__(self, tags):
        self.tags = tags

    @abstractmethod
    def fetch_articles(self):
        """Return a list of dicts with article info."""
        pass

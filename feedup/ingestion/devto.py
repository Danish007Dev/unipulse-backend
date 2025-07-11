import requests
from dateutil.parser import parse as parse_date
from .base_ingestor import BaseIngestor

DEPARTMENT_TAGS = {
    "Computer Science": ["flutter", "ai", "tools", "programming", "cloud", "linux"],
}

def assign_department(tags):
    tags = [tag.lower() for tag in tags]
    for dept, keywords in DEPARTMENT_TAGS.items():
        if any(tag in keywords for tag in tags):
            return dept
    return "Computer Science"

class DevtoIngestor(BaseIngestor):
    BASE_URL = "https://dev.to/api/articles"

    def fetch_articles(self):
        articles = []
        for tag in self.tags:
            url = f"{self.BASE_URL}?tag={tag}&top=5"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    for item in response.json():
                        tags = item.get("tags", "").split(",")
                        article_id = item["id"]
                        detail_url = f"{self.BASE_URL}/{article_id}"
                        full_content = item.get("description", "")

                        detail_response = requests.get(detail_url)
                        if detail_response.status_code == 200:
                            full_content = detail_response.json().get("body_markdown", full_content)

                        articles.append({
                            "title": item["title"],
                            "source_url": item["url"],
                            "source_name": "Dev.to",
                            "published_at": parse_date(item["published_at"]),
                            "raw_content": full_content,
                            "tag_suggestions": tags,
                            "department_name": assign_department(tags),
                        })
            except Exception as e:
                print(f"Dev.to error for tag {tag}: {e}")
        return articles

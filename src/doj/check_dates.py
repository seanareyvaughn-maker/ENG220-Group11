import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

with open(ROOT / "data" / "raw" / "doj" / "nm_collection_progress.json", encoding="utf-8") as file:
    progress = json.load(file)

articles = progress["articles"]

if articles:
    oldest = min(articles, key=lambda article: int(article["date"]))
    date = datetime.fromtimestamp(int(oldest["date"]), timezone.utc)

    print("Articles saved:", len(articles))
    print("Oldest date:", date.strftime("%Y-%m-%d"))
    print("Title:", oldest["title"])
    print("URL:", oldest["url"])
else:
    print("No articles saved yet.")
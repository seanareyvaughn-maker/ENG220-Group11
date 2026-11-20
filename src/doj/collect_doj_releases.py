import json
import time
from pathlib import Path

import requests

url = "https://www.justice.gov/api/v1/press_releases.json"

# Store both collected articles and the next page to request.
ROOT = Path(__file__).resolve().parents[2]
progress_file = ROOT / "data" / "raw" / "doj" / "nm_collection_progress.json"
pages_per_run = 200

if progress_file.exists():
    with progress_file.open("r", encoding="utf-8") as file:
        progress = json.load(file)
else:
    progress = {
        "next_page": 0,
        "records_checked": 0,
        "complete": False,
        "articles": []
    }

# Use URLs to avoid saving the same release twice.
seen_urls = {
    article["url"]
    for article in progress["articles"]
}

start_page = progress["next_page"]

if progress["complete"]:
    print("The API scan has already reached its end.")
else:
    try:
        for page in range(start_page, start_page + pages_per_run):
            response = requests.get(
                url,
                params={
                    "pagesize": 50,
                    "sort": "date",
                    "direction": "DESC",
                    "page": page
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()
            articles = data["results"]

            if not articles:
                progress["complete"] = True

                with progress_file.open("w", encoding="utf-8") as file:
                    json.dump(progress, file, indent=2, ensure_ascii=False)

                print("Reached the end of the API results.")
                break

            added = 0

            for article in articles:
                article_url = article.get("url", "")

                if (
                    "/usao-nm/pr/" in article_url
                    and article_url not in seen_urls
                ):
                    progress["articles"].append(article)
                    seen_urls.add(article_url)
                    added += 1

            progress["records_checked"] += len(articles)
            progress["next_page"] = page + 1

            # Save after every successful page.
            with progress_file.open("w", encoding="utf-8") as file:
                json.dump(progress, file, indent=2, ensure_ascii=False)

            print(
                f"Page {page}: checked {len(articles)}, "
                f"added {added}, "
                f"total saved {len(progress['articles'])}"
            )

            time.sleep(1)

    except requests.RequestException as error:
        print("Request failed:", error)
        print("Run again to resume from the last saved page.")

    except KeyboardInterrupt:
        print("\nStopped. Completed pages are saved.")

print("Total records checked:", progress["records_checked"])
print("Total NM releases saved:", len(progress["articles"]))
print("Next page:", progress["next_page"])
print("Progress saved to:", progress_file)
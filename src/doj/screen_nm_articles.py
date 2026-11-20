import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

keywords = [
    "fraud",
    "embezzl",
    "brib",
    "corrupt",
    "money laundering",
    "kickback",
    "false claims",
    " ponzi",
    "tax evasion",
    "misappropriat",
    "public funds"
]

with open(ROOT / "data" / "raw" / "doj" / "nm_collection_progress.json", "r", encoding="utf-8") as file:
    progress = json.load(file)

candidates = []

for article in progress["articles"]:
    title = article.get("title", "") or ""
    body = article.get("body", "") or ""

    # Search both the title and full article body.
    searchable_text = (title + "\n" + body).lower()

    matched_keywords = [
        keyword
        for keyword in keywords
        if keyword in searchable_text
    ]

    if matched_keywords:
        candidate = article.copy()
        candidate["matched_keywords"] = matched_keywords
        candidates.append(candidate)

        print("TITLE:", title)
        print("MATCHES:", ", ".join(matched_keywords))
        print("URL:", article.get("url", ""))
        print()

with open(ROOT / "data" / "interim" / "doj" / "nm_financial_candidates.json", "w", encoding="utf-8") as file:
    json.dump(candidates, file, indent=2, ensure_ascii=False)

print("NM releases screened:", len(progress["articles"]))
print("Potential financial misconduct releases:", len(candidates))
print("Saved to data/interim/doj/nm_financial_candidates.json")
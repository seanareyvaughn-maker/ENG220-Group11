import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]


# Convert HTML article bodies into readable text.
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("p", "div", "li", "h1", "h2", "h3"):
            self.parts.append(" ")


def clean_text(value):
    parser = TextExtractor()
    parser.feed(value or "")
    parser.close()
    return " ".join("".join(parser.parts).split())


def readable_date(value):
    try:
        return datetime.fromtimestamp(
            int(value), tz=timezone.utc
        ).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError, OSError):
        return ""


with open(ROOT / "data" / "interim" / "doj" / "nm_financial_candidates.json", "r", encoding="utf-8") as file:
    candidates = json.load(file)

columns = [
    "release_id",
    "publication_date_utc",
    "title",
    "url",
    "matched_keywords",
    "article_text",
    "relevance",
    "misconduct_category",
    "case_stage",
    "case_identifier",
    "location",
    "organization_or_sector",
    "financial_amount_notes",
    "review_notes"
]

with open(
    ROOT / "data" / "processed" / "nm_financial_review.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()

    for article in candidates:
        writer.writerow({
            "release_id": article.get("uuid", ""),
            "publication_date_utc": readable_date(article.get("date")),
            "title": clean_text(article.get("title")),
            "url": article.get("url", ""),
            "matched_keywords": ", ".join(
                article.get("matched_keywords", [])
            ),
            "article_text": clean_text(article.get("body")),
            "relevance": "",
            "misconduct_category": "",
            "case_stage": "",
            "case_identifier": "",
            "location": "",
            "organization_or_sector": "",
            "financial_amount_notes": "",
            "review_notes": ""
        })

print("Candidate releases exported:", len(candidates))
print("Saved to data/processed/nm_financial_review.csv")
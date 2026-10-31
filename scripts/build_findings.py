import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "pdf_extraction"
OUTPUT = ROOT / "data" / "processed" / "audit_findings_candidates.csv"

PATTERN = re.compile(
    r"(?P<count>\d+)\s+of\s+(?P<sample>\d+)"
    r"\s+(?P<kind>transactions|expenditures|counter withdrawals)"
    r"\s*(?:\([^)]*\))?\s*,?\s*"
    r"totaling\s+\$\s*"
    r"(?P<amount>\d+(?:,\d{3})*(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

FIELDS = [
    "source_document",
    "pdf_page",
    "label_candidate",
    "amount_usd",
    "transaction_count",
    "sample_size",
    "transaction_percent_calculated",
    "evidence",
    "review_status",
]


def main():
    rows = []
    text_files = sorted(INPUT.glob("*/page_*.txt"))

    if not text_files:
        print("No saved page-text files found. Run the PDF extractor first.")
        return

    for path in text_files:
        page_number = int(path.stem.split("_")[-1])
        text = path.read_text(encoding="utf-8")

        # Preserve bullet boundaries so nearby findings stay separate.
        blocks = re.split(r"[•]", text)

        for block in blocks:
            block = " ".join(block.split())

            for match in PATTERN.finditer(block):
                count = int(match.group("count"))
                sample = int(match.group("sample"))

                prefix = block[:match.start()].strip()

                # A preceding colon often separates the finding label.
                if ":" in prefix:
                    label = prefix.rsplit(":", 1)[0][-180:].strip()
                else:
                    label = ""

                flags = ["unreviewed"]

                if not label:
                    flags.append("check_label")

                if sample == 0 or count > sample:
                    flags.append("check_counts")

                rows.append({
                    "source_document": path.parent.name,
                    "pdf_page": page_number,
                    "label_candidate": label,
                    "amount_usd": match.group("amount").replace(",", ""),
                    "transaction_count": count,
                    "sample_size": sample,
                    "transaction_percent_calculated": (
                        round(100 * count / sample, 2)
                        if sample else ""
                    ),
                    "evidence": block,
                    "review_status": ";".join(flags),
                })

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Read {len(text_files)} saved pages.")
    print(f"Extracted {len(rows)} finding candidates.")
    print(f"Saved: {OUTPUT}")
    print("Categories can overlap. Do not sum all amounts or counts.")


if __name__ == "__main__":
    main()
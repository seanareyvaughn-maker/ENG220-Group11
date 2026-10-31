import csv
import re
from decimal import Decimal
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "pdfs"
OUTPUT = ROOT / "data" / "processed" / "pdf_extraction"

# Deliberately matches explicit dollar amounts only.
# Bare numbers in financial tables are exported separately.
MONEY = re.compile(
    r"(?P<raw>"
    r"\$\s*"
    r"(?P<number>"
    r"(?:\d[ \t]+(?=\d{1,2},\d{3}))?"
    r"(?:\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.\d{1,2})?"
    r")"
    r")"
    r"(?:[ \t]*(?P<scale>thousand|million|billion)\b)?",
    re.IGNORECASE,
)

FINDING = re.compile(r"^\s*(20\d{2}-\d{3})\b", re.MULTILINE)

AMOUNT_FIELDS = [
    "source_file",
    "pdf_page",
    "finding_id_candidate",
    "raw_amount",
    "value",
    "currency",
    "context",
    "review_status",
]

PAGE_FIELDS = [
    "source_file",
    "pdf_page",
    "character_count",
    "status",
]

TABLE_FIELDS = [
    "source_file",
    "pdf_page",
    "table_number",
    "row_number",
    "column_number",
    "cell_text",
]


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize_amount(raw, scale):
    number = re.sub(r"[^0-9.]", "", raw)
    value = Decimal(number)

    multiplier = {
        "thousand": Decimal("1000"),
        "million": Decimal("1000000"),
        "billion": Decimal("1000000000"),
    }.get((scale or "").lower(), Decimal("1"))

    return format(value * multiplier, "f")


def extract_pdf(path):
    amounts = []
    pages = []
    table_cells = []
    errors = []

    document_output = OUTPUT / path.stem
    document_output.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, start=1):
            print(f"  Page {page_number}/{total_pages}", flush=True)

            try:
                text = page.extract_text() or ""
            except Exception as error:
                errors.append(
                    f"Page {page_number}: text extraction failed: {error}"
                )
                pages.append({
                    "source_file": path.name,
                    "pdf_page": page_number,
                    "character_count": 0,
                    "status": "text_extraction_error",
                })
                page.close()
                continue

            (document_output / f"page_{page_number:03d}.txt").write_text(
                text,
                encoding="utf-8",
            )

            pages.append({
                "source_file": path.name,
                "pdf_page": page_number,
                "character_count": len(text.strip()),
                "status": (
                    "text_extracted"
                    if text.strip()
                    else "no_text_blank_or_may_need_ocr"
                ),
            })

            # Only use headings found on this page.
            # Do not carry a finding ID across pages without verification.
            finding_headings = list(FINDING.finditer(text))

            for match in MONEY.finditer(text):
                preceding = [
                    heading
                    for heading in finding_headings
                    if heading.start() <= match.start()
                ]

                finding_id = (
                    preceding[-1].group(1) if preceding else ""
                )

                context_start = max(0, match.start() - 220)
                context_end = min(len(text), match.end() + 220)
                context = " ".join(
                    text[context_start:context_end].split()
                )

                number_text = match.group("number")

                split_number = bool(
                    re.search(r"\d[ \t]+\d", number_text)
                )

                prefix = text[max(0, match.start() - 8):match.start()]
                suffix = text[match.end():match.end() + 8]

                sign_ambiguous = (
                    prefix.rstrip().endswith(("(", "-"))
                    or suffix.lstrip().startswith(")")
                )

                flags = ["unreviewed"]

                if split_number:
                    flags.append("repaired_split_number")

                if sign_ambiguous:
                    flags.append("check_sign_or_parentheses")
                
                amounts.append({
                    "source_file": path.name,
                    "pdf_page": page_number,
                    "finding_id_candidate": finding_id,
                    "raw_amount": match.group(0).strip(),
                    "value": normalize_amount(
                        match.group("raw"),
                        match.group("scale"),
                    ),
                    "currency": "USD_assumed_for_this_report",
                    "context": context,
                    "review_status": ";".join(flags),
                })

            try:
                tables = page.extract_tables()

                for table_number, table in enumerate(tables, start=1):
                    for row_number, row in enumerate(table, start=1):
                        for column_number, cell in enumerate(row, start=1):
                            table_cells.append({
                                "source_file": path.name,
                                "pdf_page": page_number,
                                "table_number": table_number,
                                "row_number": row_number,
                                "column_number": column_number,
                                "cell_text": cell or "",
                            })

            except Exception as error:
                errors.append(
                    f"Page {page_number}: table extraction failed: {error}"
                )

            page.close()

    write_csv(
        document_output / "amount_candidates.csv",
        amounts,
        AMOUNT_FIELDS,
    )

    write_csv(
        document_output / "page_status.csv",
        pages,
        PAGE_FIELDS,
    )

    write_csv(
        document_output / "table_cells.csv",
        table_cells,
        TABLE_FIELDS,
    )

    (document_output / "errors.txt").write_text(
        "\n".join(errors) if errors else "No extraction errors recorded.",
        encoding="utf-8",
    )

    return amounts, pages, table_cells


def main():
    INPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(
        path
        for path in INPUT.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdfs:
        print(f"No PDFs found. Copy your report into: {INPUT}")
        return

    all_amounts = []
    failures = []

    for path in pdfs:
        print(f"\nProcessing: {path.name}", flush=True)

        try:
            amounts, pages, cells = extract_pdf(path)
        except Exception as error:
            failures.append(f"{path.name}: {error}")
            print(f"FAILED: {error}")
            continue

        all_amounts.extend(amounts)

        print(f"  Dollar-amount candidates: {len(amounts)}")
        print(f"  Pages processed: {len(pages)}")
        print(f"  Extracted table cells: {len(cells)}")

    write_csv(
        OUTPUT / "all_amount_candidates.csv",
        all_amounts,
        AMOUNT_FIELDS,
    )

    (OUTPUT / "failed_documents.txt").write_text(
        "\n".join(failures) if failures else "No failed documents.",
        encoding="utf-8",
    )

    print(f"\nFinished. Results saved in: {OUTPUT}")
    print("Review candidates before using them in dashboard totals.")


if __name__ == "__main__":
    main()
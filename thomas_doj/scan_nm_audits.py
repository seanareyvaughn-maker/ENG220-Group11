import argparse
import csv
import io
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from pypdf import PdfReader


API_BASE = (
    "https://4re1892e77.execute-api.us-west-2.amazonaws.com/prod/"
)

# These terms are specific to the Stapleton case.
SEARCH_TERMS = [
    "Stapleton",
    "Robotics Management Learning Systems",
    "CyberQuest",
    "Ujima",
]

RESULT_COLUMNS = [
    "release_id",
    "doj_title",
    "doj_url",
    "audit_agency",
    "agency_number",
    "fiscal_year",
    "report_type",
    "audit_detail_url",
    "status",
    "pdf_file_id",
    "pdf_pages",
    "pages_without_text",
    "pdf_page",
    "matched_term",
    "excerpt",
    "error",
]


def fetch(url):
    """Download a URL, retrying temporary failures."""
    for attempt in range(3):
        request = Request(
            url,
            headers={"User-Agent": "NM-Audit-Research/1.0"},
        )

        try:
            with urlopen(request, timeout=60) as response:
                return response.read()

        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504}:
                raise
            if attempt == 2:
                raise

        except (URLError, TimeoutError):
            if attempt == 2:
                raise

        time.sleep(2 * (attempt + 1))


def api_get(endpoint, parameters):
    url = API_BASE + endpoint + "?" + urlencode(parameters)
    return json.loads(fetch(url))


def get_pdf_file_id(detail_url):
    """Resolve current and historical report detail records."""
    parsed = urlparse(detail_url)

    if parsed.hostname != "osaconnect.osa.nm.gov":
        raise ValueError("Unexpected audit detail website.")

    record_id = parse_qs(parsed.query).get("id", [""])[0]

    if not record_id:
        raise ValueError("Report detail URL has no record ID.")

    page_name = parsed.path.rsplit("/", 1)[-1]

    if page_name == "auditReportSearchDetail.html":
        details = api_get(
            "GetAuditReportDetails",
            {"type": "n", "FirmWorkflowID": record_id},
        )
        file_id = details.get("FinalReportFileGUID")

    elif page_name == "auditReportSearchDetailOld.html":
        details = api_get(
            "GetAuditReportDetailsOld",
            {"FirmWorkflowID": record_id},
        )
        file_id = details.get("pdfRFGUID")

    else:
        # Do not assume draft/other records are final public reports.
        return None

    if not file_id:
        raise ValueError("Report record has no public PDF file ID.")

    return file_id


def read_pdf(file_id):
    """Resolve the current download link and read the PDF in memory."""
    download_url = api_get(
        "GetPublicRealFileLink",
        {"GUID": file_id},
    )

    if (
        not isinstance(download_url, str)
        or not download_url.startswith("https://")
    ):
        raise ValueError("Website returned an unexpected PDF link.")

    content = fetch(download_url)

    if b"%PDF-" not in content[:1024]:
        raise ValueError("The downloaded response is not a PDF.")

    return PdfReader(io.BytesIO(content))


def compile_terms():
    patterns = []

    for term in SEARCH_TERMS:
        # Allow spaces/newlines between words and case differences.
        expression = (
            r"(?<!\w)"
            + r"\s+".join(re.escape(word) for word in term.split())
            + r"(?!\w)"
        )
        patterns.append((term, re.compile(expression, re.IGNORECASE)))

    return patterns


def scan_report(reader, patterns):
    matches = []
    pages_without_text = 0

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            pages_without_text += 1
            continue

        for term, pattern in patterns:
            for match in pattern.finditer(text):
                start = max(0, match.start() - 220)
                end = min(len(text), match.end() + 220)

                matches.append({
                    "pdf_page": page_number,
                    "matched_term": term,
                    "excerpt": text[start:end],
                })

    return matches, pages_without_text


def main():
    parser = argparse.ArgumentParser(
        description="Search candidate audit PDFs for Stapleton case terms."
    )
    parser.add_argument("input_csv")
    parser.add_argument("--output", default="nm_audit_text_results.csv")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum reports to process; 0 means all selected reports.",
    )
    args = parser.parse_args()

    from pathlib import Path

    if Path(args.input_csv).resolve() == Path(args.output).resolve():
        parser.error("Output must be different from the input file.")

    with open(args.input_csv, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required = {"doj_title", "audit_detail_url", "audit_agency"}
        missing = required - set(reader.fieldnames or [])

        if missing:
            parser.error("Missing columns: " + ", ".join(sorted(missing)))

        # This scanner's terms apply only to the Stapleton case.
        candidates = [
            row for row in reader
            if "stapleton" in row.get("doj_title", "").casefold()
            or "stapleton" in row.get("agency_search", "").casefold()
            or (
                "former new mexico state representative"
                in row.get("doj_title", "").casefold()
                and "bribery" in row.get("doj_title", "").casefold()
            )
        ]

    # Begin with 2021, the final year of the conduct in this case.
    candidates.sort(
        key=lambda row: (
            row.get("fiscal_year") != "2021",
            row.get("fiscal_year", ""),
            row.get("audit_agency", ""),
        )
    )

    if args.limit > 0:
        candidates = candidates[:args.limit]

    patterns = compile_terms()
    matching_reports = 0
    errors = 0
    skipped = 0

    print(f"Selected {len(candidates)} candidate reports.", flush=True)

    with open(args.output, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        writer.writeheader()

        for index, candidate in enumerate(candidates, start=1):
            base = {
                key: candidate.get(key, "")
                for key in RESULT_COLUMNS
                if key in candidate
            }

            print(
                f"\n[{index}/{len(candidates)}] "
                f"{candidate.get('audit_agency')} — "
                f"{candidate.get('fiscal_year')}",
                flush=True,
            )

            try:
                file_id = get_pdf_file_id(candidate["audit_detail_url"])

                if file_id is None:
                    writer.writerow({
                        **base,
                        "status": "skipped_report_type",
                    })
                    skipped += 1
                    print("Skipped draft/unsupported report type.", flush=True)
                    continue

                base["pdf_file_id"] = file_id

                pdf = read_pdf(file_id)
                matches, blank_pages = scan_report(pdf, patterns)

                base["pdf_pages"] = len(pdf.pages)
                base["pages_without_text"] = blank_pages

                if matches:
                    matching_reports += 1

                    for match in matches:
                        writer.writerow({
                            **base,
                            **match,
                            "status": "term_found_review_required",
                        })

                    print(
                        f"Found {len(matches)} term occurrences.",
                        flush=True,
                    )

                else:
                    status = (
                        "no_terms_found_incomplete_text"
                        if blank_pages
                        else "no_terms_found_in_extracted_text"
                    )

                    writer.writerow({**base, "status": status})
                    print("No search terms found in extracted text.", flush=True)

                if blank_pages:
                    print(
                        f"{blank_pages} pages had no extracted text; "
                        "they may need OCR.",
                        flush=True,
                    )

            except Exception as error:
                # Record failure and continue to the next report.
                errors += 1
                writer.writerow({
                    **base,
                    "status": "error",
                    "error": f"{type(error).__name__}: {error}",
                })
                print(f"ERROR: {error}", flush=True)

            finally:
                file.flush()
                time.sleep(1)

    print(f"\nReports with term matches: {matching_reports}")
    print(f"Reports skipped: {skipped}")
    print(f"Errors: {errors}")
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
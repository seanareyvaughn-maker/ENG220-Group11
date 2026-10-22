import argparse
import csv
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# Public search endpoint used by the NM State Auditor website.
API_URL = (
    "https://4re1892e77.execute-api.us-west-2.amazonaws.com/"
    "prod/GetAuditReportList"
)

SITE_URL = "https://osaconnect.osa.nm.gov/"

# Each rule connects a DOJ case to an agency search.
# Add more rules here as we identify the agencies in other releases.
CASE_SEARCHES = [
    {
        "case_term": "Stapleton",
        "agency_search": "Albuquerque Public",
    },
]

# The website uses different detail pages for different record types.
DETAIL_PAGES = {
    "n": "auditReportSearchDetail.html",
    "o": "auditReportSearchDetailOld.html",
    "d": "auditReportSearchDetailDraft.html",
    "f": "auditReportSearchDetail5Day.html",
    "c": "auditReportSearchDetailCert.html",
}

OUTPUT_COLUMNS = [
    "release_id",
    "doj_title",
    "doj_url",
    "agency_search",
    "search_status",
    "audit_agency",
    "agency_number",
    "fiscal_year",
    "report_type",
    "audit_detail_url",
    "error",
]


def read_releases(filename):
    """Read the existing DOJ CSV without changing it."""
    with open(filename, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required = {"release_id", "title", "url", "article_text"}
        missing = required - set(reader.fieldnames or [])

        if missing:
            raise ValueError(
                "Missing required columns: " + ", ".join(sorted(missing))
            )

        return list(reader)


def search_audits(agency_name):
    """Search only for the requested agency."""
    parameters = {
        "searchTerm": agency_name,
        "financialStatementOpinion": "",
        "opinionForMajorFederalPrograms": "",
        "fyInit": "",
        "fyEnd": "",
        "summary": "1",
    }

    request = Request(
        API_URL + "?" + urlencode(parameters),
        headers={
            "User-Agent": "NM-Audit-Research/1.0",
            "Accept": "application/json",
        },
    )

    # Retry temporary connection/server problems.
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                records = json.load(response)

            if not isinstance(records, list):
                raise ValueError("Audit website returned an unexpected format.")

            if any(not isinstance(record, dict) for record in records):
                raise ValueError("Audit website returned invalid report records.")

            return records

        except HTTPError as error:
            temporary = error.code in {429, 500, 502, 503, 504}
            if not temporary or attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))

        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def make_detail_url(audit):
    """Build the report detail link using the website's record ID."""
    page = DETAIL_PAGES.get(audit.get("type"))
    record_id = audit.get("FirmWorkFlowID")

    if not page or not record_id:
        return ""

    return SITE_URL + page + "?" + urlencode({"id": record_id})


def main():
    parser = argparse.ArgumentParser(
        description="Search NM audits for cases in an existing DOJ CSV."
    )
    parser.add_argument("input_csv", help="Your existing DOJ review CSV")
    parser.add_argument(
        "--output",
        default="nm_audit_candidates.csv",
        help="Output filename",
    )
    args = parser.parse_args()

    # Prevent accidentally replacing the input file.
    from pathlib import Path

    if Path(args.input_csv).resolve() == Path(args.output).resolve():
        parser.error("The output must be different from the input CSV.")

    releases = read_releases(args.input_csv)

    print(f"Loaded {len(releases)} DOJ releases.", flush=True)

    # Reuse an agency's results if multiple releases concern that agency.
    cache = {}
    matched_releases = set()
    result_count = 0

    with open(args.output, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for release in releases:
            searchable_text = (
                release["title"] + " " + release["article_text"]
            ).casefold()

            for rule in CASE_SEARCHES:
                if rule["case_term"].casefold() not in searchable_text:
                    continue

                agency = rule["agency_search"]
                matched_releases.add(release["release_id"])

                base_row = {
                    "release_id": release["release_id"],
                    "doj_title": release["title"],
                    "doj_url": release["url"],
                    "agency_search": agency,
                }

                print(f"\nDOJ: {release['title']}", flush=True)
                print(f"Searching audits for: {agency}", flush=True)

                try:
                    if agency not in cache:
                        cache[agency] = search_audits(agency)

                    audits = cache[agency]

                except (HTTPError, URLError, TimeoutError, ValueError) as error:
                    writer.writerow({
                        **base_row,
                        "search_status": "search_error",
                        "error": str(error),
                    })
                    file.flush()
                    print(f"Search failed: {error}", flush=True)
                    continue

                print(f"Found {len(audits)} candidate records.", flush=True)

                if not audits:
                    writer.writerow({
                        **base_row,
                        "search_status": "no_agency_results",
                    })

                for audit in audits:
                    writer.writerow({
                        **base_row,
                        "search_status": "agency_candidate_unverified",
                        "audit_agency": audit.get("Name", ""),
                        "agency_number": audit.get("Number", ""),
                        "fiscal_year": audit.get("FiscalYear", ""),
                        "report_type": audit.get("ReportType", ""),
                        "audit_detail_url": make_detail_url(audit),
                    })
                    result_count += 1

                file.flush()

    print(f"\nDOJ releases selected: {len(matched_releases)}")
    print(f"Candidate audit rows saved: {result_count}")
    print(f"Output: {args.output}")
    print("Other releases were not searched by this first version.")


if __name__ == "__main__":
    main()
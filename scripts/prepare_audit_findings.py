import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "audit_findings_candidates.csv"
OUTPUT = ROOT / "data" / "processed" / "audit_findings_grouped.csv"

# These mappings apply only to this Village of Cuba report.
PAGE_GROUPS = {
    185: ("Expenditure testing", 60),
    186: ("Check-image testing", 137),
    187: ("Counter withdrawals", 23),
    200: ("Credit-card testing", 88),
    201: ("Credit-card testing", 88),
}

REPORT_NAME = "Village of Cuba Special Audit (Consulting Procedures) Report_2026 0511"


def main():
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        original_fields = reader.fieldnames
        rows = list(reader)

    fields = original_fields + [
        "testing_group",
        "record_type",
        "group_assignment_status",
        "interpretation_note",
    ]

    for row in rows:
        page = int(row["pdf_page"])
        sample = int(row["sample_size"])

        group, expected_sample = PAGE_GROUPS.get(
            page, ("Unassigned", None)
        )

        correct_report = row["source_document"] == REPORT_NAME

        if correct_report and sample == expected_sample:
            row["testing_group"] = group
            row["group_assignment_status"] = (
                "report_specific_page_and_sample_mapping"
            )
        else:
            row["testing_group"] = "Unassigned"
            row["group_assignment_status"] = "needs_review"

        label = row["label_candidate"].strip().lower()

        row["record_type"] = (
            "Supported transactions"
            if label == "properly supported transactions"
            else "Exception or concern"
        )

        row["interpretation_note"] = (
            "Categories may overlap. Do not sum category amounts "
            "or counts. Results describe the tested sample, not "
            "proven theft or the entire transaction population."
        )

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    groups = sorted({row["testing_group"] for row in rows})

    for group in groups:
        count = sum(row["testing_group"] == group for row in rows)
        print(f"{group}: {count} category rows")

    print(f"\nSaved: {OUTPUT}")
    print("Review status remains unchanged; records are not yet verified.")


if __name__ == "__main__":
    main()
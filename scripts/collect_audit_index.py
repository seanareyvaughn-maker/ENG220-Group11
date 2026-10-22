import json
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://4re1892e77.execute-api.us-west-2.amazonaws.com"
    "/prod/GetAuditReportList"
)

params = {
    "searchTerm": "Cuba",
    "financialStatementOpinion": "",
    "opinionForMajorFederalPrograms": "",
    "fyInit": "-1",
    "fyEnd": "",
    "summary": "1",
}

root = Path(__file__).resolve().parents[1]
output = root / "data" / "raw"
output.mkdir(parents=True, exist_ok=True)

response = requests.get(URL, params=params, timeout=60)
response.raise_for_status()

records = response.json()

if not isinstance(records, list):
    raise ValueError(
        f"Expected a JSON list, received {type(records).__name__}. "
        "Inspect the response before continuing."
    )

if not all(isinstance(record, dict) for record in records):
    raise ValueError("The response contains unexpected record types.")

json_file = output / "cuba_audit_index.json"
csv_file = output / "cuba_audit_index.csv"

json_file.write_text(
    json.dumps(records, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

df = pd.DataFrame(records)
df.to_csv(csv_file, index=False, encoding="utf-8-sig")

print(f"Saved {len(df)} records.")

if not df.empty:
    columns = [
        column
        for column in ["Name", "FiscalYear", "ReportType"]
        if column in df.columns
    ]
    print(df[columns].to_string(index=False))
else:
    print("No records returned. Compare the search with the website.")
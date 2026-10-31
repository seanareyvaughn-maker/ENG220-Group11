from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
output = root / "data" / "processed"
output.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    root / "data" / "raw" / "cuba_audit_index.csv",
    encoding="utf-8-sig",
    dtype={"FirmWorkFlowID": "string", "Number": "string"},
)

df["FiscalYear"] = pd.to_numeric(
    df["FiscalYear"], errors="raise"
).astype("Int64")

# Count each indexed report identifier only once.
df = df.drop_duplicates(subset=["FirmWorkFlowID"])

reports_by_entity_year = (
    df.groupby(["Name", "FiscalYear"])
    .size()
    .reset_index(name="report_count")
)

reports_by_type = (
    df.assign(ReportType=df["ReportType"].fillna("Not recorded"))
    .groupby("ReportType")
    .size()
    .reset_index(name="report_count")
)

reports_by_entity_year.to_csv(
    output / "audit_reports_by_entity_year.csv", index=False
)
reports_by_type.to_csv(
    output / "audit_reports_by_type.csv", index=False
)

print(reports_by_entity_year.to_string(index=False))
print(reports_by_type.to_string(index=False))
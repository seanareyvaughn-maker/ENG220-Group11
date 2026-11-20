# Financial Transparency and Corruption Research
ENG 220 — Group 11

## Overview
This project explores public financial records and documented
accountability issues in New Mexico through data collection,
analysis, and an interactive Streamlit dashboard.

The dashboard presents three research areas:
- Capital Appropriations
- DOJ Releases
- Audit Findings

## Dashboard Features

### Capital Appropriations
- Search appropriation IDs, project titles, entities, and cities
- Filter by county and appropriation year
- Explore records flagged by screening rules adapted from the team's
  MATLAB analysis
- Compare reported amounts for individual records
- Download filtered records and screening flags

### DOJ Releases
- Search collected press-release titles and article text
- Filter by matched keywords and publication dates
- View release details and available team review fields
- Open original DOJ source links
- Download filtered records

### Audit Findings
- Explore extracted audit records by testing group
- View transaction counts, calculated percentages, and reported amounts
- Read supporting text and PDF page references
- Download selected records

### Interface Demo
An optional demo uses clearly labeled synthetic data to test charts
and filters. It is disabled by default and is separate from the
research datasets.

## Repository Structure
```
app.py                 Streamlit dashboard
requirements.txt       Python dependencies
data/
  raw/                 Collected, unmodified inputs
    appropriations/    NM capital appropriations CSV
    audits/            Cuba audit index (JSON/CSV)
    doj/               DOJ press-release collections
    fac/               FAC summary export
  interim/doj/         Intermediate DOJ screening output
  processed/           Cleaned datasets the dashboard reads
src/
  audits/              Audit index, PDF extraction, findings, FAC figures
  doj/                 DOJ release collection, screening, and export
  nm_audits/           Search/scan State Auditor reports for DOJ cases
matlab/                MATLAB analysis (appropriations and audit findings)
figures/               Charts and screenshots from the analysis
docs/                  Project report, sources, and data notes
```

### Data pipeline
- **Audits:** `src/audits/collect_audit_index.py` -> `extract_audit_pdfs.py` ->
  `build_findings.py` -> `prepare_audit_findings.py` -> `data/processed/audit_findings_grouped.csv`
- **DOJ:** `src/doj/collect_doj_releases.py` -> `screen_nm_articles.py` ->
  `export_nm_review.py` -> `data/processed/nm_financial_review.csv`
- **Appropriations:** `data/raw/appropriations/` CSV, analyzed in `matlab/unmatched_appropriations.m`

Run scripts from the repository root, for example `python src/doj/export_nm_review.py`.
Large files that are not in the repository are described in `docs/data_notes.md`.

## Setup
From the repository's root directory, create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Running the Dashboard
From the repository's root directory, run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If your virtual environment is already activated, use:

```powershell
python -m streamlit run app.py
```

## Dashboard Data Inputs
The dashboard reads these repository files:
- `data/raw/appropriations/nm-capital-appropriations-2026-10-13.csv`
- `data/processed/nm_financial_review.csv`
- `data/processed/audit_findings_grouped.csv`

The dashboard reads existing outputs; launching it does not run the
collection scripts or modify teammate research files.

## Validation Status
A local comparison tested 7,773 appropriation records against a
float64 Python reference calculation.

Results:
- Amount mismatch flags: 0
- Negative-value flags after the reauthorization exclusion: 57
- Zero-appropriation-with-activity flags: 0
- Different flag decisions between implementations: 0
- Missing or invalid values in the four tested financial inputs: 0

This comparison did not execute MATLAB or independently verify the
source records. Direct comparison against MATLAB output remains pending.

## Interpretation and Limitations
- Screening flags identify records for review, not proven accounting
  errors, losses, or corruption.
- DOJ keyword matches do not establish project relevance or misconduct.
- Press releases may describe allegations, settlements, convictions,
  or other proceedings; these categories must remain distinct.
- DOJ record counts are not counts of unique cases or defendants.
- Audit extraction records have not been independently verified.
- Audit categories may overlap; counts, percentages, and amounts
  should not be added together as if they represent distinct transactions.
- Audit percentages describe transaction counts, not percentages of dollars.
- Parent/sub-appropriation relationships require review before
  calculating aggregate financial totals.
- The datasets should not be combined into one corruption count or
  total of proven financial losses.

## Project Status
In development. All three research sections are connected to the
dashboard. Source verification, dataset review, and final documentation
remain in progress.

## Sources
See `docs/sources.md` and the dashboard's Data & Methodology tab.
#!/usr/bin/env python3
"""
fac_cuba_figures.py
-------------------
Graphs for the Cuba, NM finance / corruption-risk project, built from the three
FAC bulk files:  general.csv, federal_awards.csv, findings.csv

How this differs from the first MATLAB version
  * A finding is linked to the program it was actually reported on
    (report_id + award_reference), not to every program in an audit that had
    any finding.
  * Each finding is counted once (report_id + reference_number).
  * Dollars are split by what happened to THAT program's award line:
    material weakness / significant deficiency / other finding / no finding.
  * Cuba vs New Mexico is normalised (per audit) and ignores the newest audit
    year if it is still mostly unfiled.
  * Linear axes, zero years shown, and the number of audits written on the chart.

Run
    python fac_cuba_figures.py --data-dir path/to/folder/with/the/csvs

Options
    --out-dir figures                    where the PNGs and tables go
    --state NM --city CUBA               which auditees count as "Cuba"
    --name-regex "VILLAGE OF CUBA|CUBA INDEPENDENT"
                                         keep only matching entity names
                                         (use this to separate the Village and
                                         the school district from other
                                         auditees that have a Cuba address)

Needs: pandas, matplotlib, numpy      (pip install pandas matplotlib numpy)

A finding is a reported audit issue, not proof of fraud or loss.
"""

import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Look: one surface, three inks, hairline grid. Colours follow the entity
# (an agency or a severity keeps its colour in every chart).
# --------------------------------------------------------------------------
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"

# Federal agency prefix -> (name, colour). Fixed slots, never re-assigned by rank.
AGENCIES = {
    "15": ("Interior (incl. Bureau of Indian Education)", "#2a78d6"),
    "84": ("Education", "#eb6834"),
    "10": ("Agriculture (school meals)", "#1baf7a"),
    "21": ("Treasury", "#eda100"),
    "14": ("Housing & Urban Development", "#e87ba4"),
    "66": ("EPA", "#008300"),
}
OTHER_AGENCY = ("Other agencies", BASELINE)

# Severity is ordered, so it gets one hue, dark = more serious. "No finding" is neutral.
SEVERITY = ["Material weakness", "Significant deficiency", "Other finding"]
STATUS = SEVERITY + ["No finding"]
SEV_COLOUR = {
    "Material weakness": "#104281",
    "Significant deficiency": "#3987e5",
    "Other finding": "#86b6ef",
    "No finding": BASELINE,
}
CUBA_COLOUR, NM_COLOUR = "#2a78d6", MUTED


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 11, "text.color": INK,
        "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "axes.edgecolor": BASELINE, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.major.size": 0, "ytick.major.size": 0,
    })


def tidy(ax, grid="y"):
    ax.set_axisbelow(True)
    ax.grid(axis=grid, color=GRID, linewidth=0.8, linestyle="-")
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)


def finish(fig, title, subtitle, note, path, top=0.84, bottom=0.12, left=None):
    fig.subplots_adjust(top=top, bottom=bottom, **({"left": left} if left else {}))
    fig.text(0.01, 0.985, title, ha="left", va="top", fontsize=15,
             fontweight="bold", color=INK)
    fig.text(0.01, 0.935, textwrap.fill(subtitle, 120), ha="left", va="top",
             fontsize=10.5, color=INK2)
    fig.text(0.01, 0.01, textwrap.fill(note, 150), ha="left", va="bottom",
             fontsize=8.5, color=MUTED)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def header(path):
    return list(pd.read_csv(path, nrows=0).columns)


def need(cols, required, name, path):
    missing = [c for c in required if c not in cols]
    if missing:
        sys.exit(f"\n{name} ({path}) is missing column(s): {missing}\n"
                 f"Columns it has: {cols}\n"
                 "Check the FAC data dictionary and rename the column in this script.")


def find_file(folder, name):
    p = Path(folder) / name
    if not p.exists():
        sys.exit(f"Could not find {p}. Use --data-dir to point at the folder with the CSVs.")
    return p


def load_general(path):
    cols = header(path)
    req = ["report_id", "audit_year", "auditee_name", "auditee_city", "auditee_state"]
    need(cols, req, "general.csv", path)
    use = req + [c for c in ["auditee_uei", "auditee_ein", "resubmission_status"] if c in cols]
    g = pd.read_csv(path, usecols=use, dtype=str, low_memory=False)
    g["audit_year"] = pd.to_numeric(g["audit_year"], errors="coerce")
    g = g.dropna(subset=["audit_year", "report_id"])
    g["audit_year"] = g["audit_year"].astype(int)
    if "resubmission_status" in g:  # drop reports that were replaced by a resubmission
        g = g[g["resubmission_status"].fillna("").str.lower() != "deprecated"]
    return g.drop_duplicates("report_id")


def load_filtered(path, ids, wanted, required, name):
    """Read a big CSV in chunks, keeping only rows whose report_id is in `ids`."""
    cols = header(path)
    need(cols, required, name, path)
    use = [c for c in wanted if c in cols]
    parts = []
    for chunk in pd.read_csv(path, usecols=use, dtype=str, chunksize=400_000):
        parts.append(chunk[chunk["report_id"].isin(ids)])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=use)


def yes(s):
    return s.fillna("").astype(str).str.strip().str.upper().isin({"Y", "YES", "TRUE", "T", "1"})


def clean_program(s):
    s = " ".join(str(s).replace("_", " - ").split()).title()
    for w in (" To ", " Of ", " And ", " For ", " The ", " In ", " On ", " Or "):
        s = s.replace(w, w.lower())
    return s.replace("Bia ", "BIA ").replace("Isep", "ISEP")


def short(s, n=50):
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def year_labels(years, aud, last_complete):
    out = []
    for y in years:
        n = int(aud.get(y, 0))
        out.append(f"{y}{'*' if y > last_complete else ''}\n{n} audit{'s' if n != 1 else ''}")
    return out


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
NOTE = ("Source: Federal Audit Clearinghouse bulk data. A finding is a reported audit issue, "
        "not proof of fraud or loss. Federal awards only: local (general fund) spending is not in this data.")


def fig_spending(a, scope, years, aud, last_complete, label, out):
    d = a.merge(scope[["report_id", "audit_year"]], on="report_id")
    d["key"] = d["agency_prefix"].where(d["agency_prefix"].isin(AGENCIES), "other")
    pv = (d.pivot_table(index="audit_year", columns="key", values="amount", aggfunc="sum")
          .reindex(years).fillna(0.0) / 1e6)
    order = [k for k in AGENCIES if k in pv.columns] + (["other"] if "other" in pv.columns else [])

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    x = np.arange(len(years))
    bottom = np.zeros(len(years))
    for k in order:
        name, col = AGENCIES.get(k, OTHER_AGENCY)
        ax.bar(x, pv[k].values, bottom=bottom, width=0.62, color=col,
               edgecolor=SURFACE, linewidth=1.5, label=name)
        bottom += pv[k].values
    for xi, tot in zip(x, bottom):
        if tot > 0:
            ax.text(xi, tot + bottom.max() * 0.012, f"${tot:,.1f}M", ha="center",
                    va="bottom", fontsize=9, color=INK2)
    ax.set_xticks(x, year_labels(years, aud, last_complete), fontsize=9)
    ax.set_ylabel("Federal dollars spent ($ millions)")
    ax.set_ylim(0, max(bottom.max() * 1.12, 1))
    tidy(ax, "y")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=10)
    finish(fig, "Federal dollars spent by audit year and agency",
           f"{label}. Each bar adds up the federal money those audits report spending that year.",
           NOTE + "  * Newest audit year: audits are still being filed.",
           out, top=0.86, bottom=0.14)


def fig_findings_by_year(uf_scope, scope, years, aud, last_complete, label, out):
    cnt = (uf_scope.pivot_table(index="audit_year", columns="severity",
                                values="reference_number", aggfunc="count", fill_value=0)
           .reindex(index=years, columns=SEVERITY, fill_value=0))
    fig, ax = plt.subplots(figsize=(11.5, 6.0))
    x = np.arange(len(years))
    bottom = np.zeros(len(years))
    for s in SEVERITY:
        ax.bar(x, cnt[s].values, bottom=bottom, width=0.62, color=SEV_COLOUR[s],
               edgecolor=SURFACE, linewidth=1.5, label=s)
        bottom += cnt[s].values
    ymax = max(bottom.max(), 1)
    for xi, y, tot in zip(x, years, bottom):
        if tot > 0:
            ax.text(xi, tot + ymax * 0.02, f"{int(tot)}", ha="center", va="bottom",
                    fontsize=9.5, color=INK2)
        elif aud.get(y, 0) > 0:  # audited, nothing found: say so explicitly
            ax.text(xi, ymax * 0.02, "0", ha="center", va="bottom", fontsize=9.5, color=MUTED)
    ax.set_xticks(x, year_labels(years, aud, last_complete), fontsize=9)
    ax.set_ylabel("Findings (each counted once)")
    ax.set_ylim(0, ymax * 1.2)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    tidy(ax, "y")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=3, frameon=False, fontsize=10)
    finish(fig, "Audit findings by audit year",
           f"{label}. A '0' means the entity was audited and nothing was reported; "
           "the audit count under each year shows whether anyone was audited at all.",
           NOTE + "  * Newest audit year: audits are still being filed.",
           out, top=0.80, bottom=0.14)


def barh_stack(ax, labels, columns, colours, names):
    y = np.arange(len(labels))
    left = np.zeros(len(labels))
    for c, col, nm in zip(columns, colours, names):
        ax.barh(y, c, left=left, height=0.62, color=col, edgecolor=SURFACE,
                linewidth=1.5, label=nm)
        left += c
    ax.set_yticks(y, labels, fontsize=10)
    return left


def fig_findings_by_program(pairs, label, out, top_n=12):
    if pairs.empty:
        print("  (no findings are linked to a program - skipping the by-program chart)")
        return
    pv = (pairs.pivot_table(index="program", columns="severity", values="reference_number",
                            aggfunc="count", fill_value=0)
          .reindex(columns=SEVERITY, fill_value=0))
    pv["total"] = pv.sum(axis=1)
    pv = pv.sort_values(["total"], ascending=False).head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11.5, 0.5 * len(pv) + 3.4))
    tips = barh_stack(ax, [short(p) for p in pv.index], [pv[s].values for s in SEVERITY],
                      [SEV_COLOUR[s] for s in SEVERITY], SEVERITY)
    for yi, t in enumerate(tips):
        ax.text(t + max(tips.max(), 1) * 0.015, yi, f"{int(t)}", va="center", fontsize=9.5, color=INK2)
    ax.set_xlim(0, max(tips.max() * 1.12, 1))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Findings reported on that program")
    tidy(ax, "x")
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    finish(fig, "Which programs the findings were reported on",
           f"{label}. Each finding is attached to the program(s) it names (award_reference). "
           "A finding that names two programs is counted once in each.",
           NOTE, out, top=0.84, bottom=0.17, left=0.32)


def fig_dollars_by_program(a, label, out, table_out, top_n=12):
    pv = (a.pivot_table(index="program", columns="award_severity", values="amount", aggfunc="sum")
          .reindex(columns=STATUS).fillna(0.0) / 1e6)
    pv["total"] = pv.sum(axis=1)
    pv["share_with_finding"] = 1 - pv["No finding"] / pv["total"].replace(0, np.nan)
    pv.sort_values("total", ascending=False).to_csv(table_out, float_format="%.4f")
    overall = 1 - pv["No finding"].sum() / pv["total"].sum() if pv["total"].sum() else float("nan")
    top = pv.sort_values("total", ascending=False).head(top_n).iloc[::-1]

    fig, ax = plt.subplots(figsize=(11.5, 0.5 * len(top) + 3.4))
    tips = barh_stack(ax, [short(p) for p in top.index], [top[s].values for s in STATUS],
                      [SEV_COLOUR[s] for s in STATUS], STATUS)
    for yi, t in enumerate(tips):
        ax.text(t + tips.max() * 0.012, yi, f"${t:,.1f}M", va="center", fontsize=9.5, color=INK2)
    ax.set_xlim(0, tips.max() * 1.12)
    ax.set_xlabel("Federal dollars spent ($ millions), all audit years in the data combined")
    tidy(ax, "x")
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    finish(fig, "Federal dollars by program, split by what the audit found on that program",
           f"{label}. Overall, {overall:.0%} of these dollars were spent on awards that had at least one "
           "reported finding. Shading is the most serious finding on that program's award.",
           NOTE, out, top=0.84, bottom=0.15, left=0.32)
    return overall


def fig_benchmark(scope, nm, uf_nm, last_complete, label, out, table_out):
    windows = [("Latest complete year", 1), ("Last 5 complete years", 5), ("Last 10 complete years", 10)]
    rows = []
    for wl, n in windows:
        lo = last_complete - n + 1
        for who, g in (("Cuba", scope), ("New Mexico", nm)):
            ids = set(g[(g.audit_year >= lo) & (g.audit_year <= last_complete)].report_id)
            fs = uf_nm[uf_nm.report_id.isin(ids)]
            na = len(ids)
            first = max(lo, int(nm.audit_year.min()))
            rows.append(dict(window=wl, years=(str(last_complete) if first == last_complete
                                               else f"{first}-{last_complete}"),
                             who=who, audits=na, audits_with_finding=fs.report_id.nunique(),
                             audits_with_material_weakness=fs[fs.severity == "Material weakness"].report_id.nunique(),
                             findings=len(fs)))
    t = pd.DataFrame(rows)
    t["share_audits_with_finding"] = t.audits_with_finding / t.audits.replace(0, np.nan)
    t["findings_per_audit"] = t.findings / t.audits.replace(0, np.nan)
    t.to_csv(table_out, index=False, float_format="%.4f")

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.0))
    x = np.arange(len(windows))
    w = 0.34
    for ax, metric, fmt, ttl in (
        (axes[0], "share_audits_with_finding", lambda v: f"{v:.0%}", "Share of audits with at least one finding"),
        (axes[1], "findings_per_audit", lambda v: f"{v:.2f}", "Findings per audit"),
    ):
        vmax = 0
        for off, who, col in ((-w / 2, "Cuba", CUBA_COLOUR), (w / 2, "New Mexico", NM_COLOUR)):
            vals = t[t.who == who][metric].fillna(0).values
            ax.bar(x + off, vals, width=w, color=col, edgecolor=SURFACE, linewidth=1.5, label=who)
            vmax = max(vmax, vals.max())
            for xi, v in zip(x + off, vals):
                ax.text(xi, v + 0.01 * max(vmax, 1), fmt(v), ha="center", va="bottom", fontsize=9.5, color=INK2)
        ax.set_ylim(0, max(vmax * 1.2, 0.05))
        ticks = []
        for wl, _ in windows:
            c = t[(t.window == wl) & (t.who == "Cuba")].iloc[0]
            s = t[(t.window == wl) & (t.who == "New Mexico")].iloc[0]
            ticks.append(f"{wl}\n{c.years}\nCuba n={int(c.audits)} · NM n={int(s.audits)}")
        ax.set_xticks(x, ticks, fontsize=8.5)
        ax.set_title(ttl, loc="left", fontsize=11.5, color=INK, pad=10)
        if metric == "share_audits_with_finding":
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
        tidy(ax, "y")
    handles, names = axes[0].get_legend_handles_labels()
    fig.legend(handles, names, loc="upper right", bbox_to_anchor=(0.99, 0.985), ncols=2,
               frameon=False, fontsize=10.5)
    finish(fig, "How Cuba compares with New Mexico",
           f"{label} vs. all New Mexico auditees (which include Cuba). Complete audit years only; "
           "n = number of audits. Rates, not raw counts, so a town and a state can be compared.",
           NOTE, out, top=0.82, bottom=0.17)
    return t


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=".")
    ap.add_argument("--out-dir", default="fac_figures")
    ap.add_argument("--state", default="NM")
    ap.add_argument("--city", default="CUBA")
    ap.add_argument("--name-regex", default="")
    args = ap.parse_args()
    state, city = args.state.upper().strip(), args.city.upper().strip()

    style()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Loading general.csv ...")
    general = load_general(find_file(args.data_dir, "general.csv"))
    nm = general[general.auditee_state.fillna("").str.upper().str.strip() == state]
    scope = nm[nm.auditee_city.fillna("").str.upper().str.strip() == city]
    if args.name_regex:
        scope = scope[scope.auditee_name.str.contains(args.name_regex, case=False, regex=True, na=False)]
    if scope.empty:
        sys.exit(f"No audits found for city={city}, state={state}, name-regex={args.name_regex!r}.")
    label = (f"Auditees matching “{args.name_regex}” in {city.title()}, {state}" if args.name_regex
             else f"Auditees with a {city.title()}, {state} address")

    # Who is "Cuba"? Look at this table before presenting.
    ent = (scope.groupby("auditee_name")
           .agg(audits=("report_id", "nunique"), first_year=("audit_year", "min"),
                last_year=("audit_year", "max")).sort_values("audits", ascending=False))
    ent.to_csv(out / "entities_in_scope.csv")
    print(f"\nEntities in scope ({len(scope)} audits):")
    print(ent.to_string())

    # Which audit years are complete? A year with < half the typical NM count is still being filed.
    nm_per_year = nm.groupby("audit_year").report_id.nunique().sort_index()
    typical = nm_per_year.median()
    last_complete = int(nm_per_year[nm_per_year >= 0.5 * typical].index.max())
    years = list(range(int(scope.audit_year.min()), int(scope.audit_year.max()) + 1))
    aud = scope.groupby("audit_year").report_id.nunique()
    print(f"\nLatest complete audit year: {last_complete} "
          f"(NM audits per year: { {int(k): int(v) for k, v in nm_per_year.items()} })")

    print("\nLoading findings.csv ...")
    f_cols = ["report_id", "reference_number", "award_reference", "is_material_weakness",
              "is_significant_deficiency", "is_questioned_costs", "is_repeat_finding",
              "is_other_findings", "type_requirement"]
    f_rows = load_filtered(find_file(args.data_dir, "findings.csv"), set(nm.report_id), f_cols,
                           ["report_id", "reference_number", "award_reference", "is_material_weakness"],
                           "findings.csv")
    f_rows["reference_number"] = f_rows["reference_number"].fillna("(none)")
    for c in ("is_material_weakness", "is_significant_deficiency", "is_questioned_costs", "is_repeat_finding"):
        f_rows[c] = yes(f_rows[c]) if c in f_rows else False

    # One row per finding (report_id + reference_number); strongest flag wins.
    uf = (f_rows.groupby(["report_id", "reference_number"], as_index=False)
          .agg(mw=("is_material_weakness", "max"), sd=("is_significant_deficiency", "max"),
               questioned_costs=("is_questioned_costs", "max"), repeat=("is_repeat_finding", "max")))
    uf["severity"] = np.select([uf.mw, uf.sd], SEVERITY[:2], default=SEVERITY[2])
    uf = uf.merge(nm[["report_id", "audit_year", "auditee_name"]], on="report_id", how="left")
    uf_scope = uf[uf.report_id.isin(scope.report_id)]

    print("Loading federal_awards.csv ...")
    a_cols = ["report_id", "award_reference", "federal_program_name", "amount_expended",
              "federal_agency_prefix"]
    a = load_filtered(find_file(args.data_dir, "federal_awards.csv"), set(scope.report_id), a_cols,
                      ["report_id", "award_reference", "federal_program_name", "amount_expended"],
                      "federal_awards.csv")
    a["amount"] = pd.to_numeric(a["amount_expended"], errors="coerce").fillna(0.0)
    a["program"] = a["federal_program_name"].fillna("(unnamed program)").map(clean_program)
    a["agency_prefix"] = (a["federal_agency_prefix"].fillna("").str.strip()
                          if "federal_agency_prefix" in a else "NA")

    # Link findings to award lines (the fix for the first MATLAB graphs).
    fr = f_rows[f_rows.report_id.isin(scope.report_id)].dropna(subset=["award_reference"])
    link = (fr.groupby(["report_id", "award_reference"], as_index=False)
            .agg(mw=("is_material_weakness", "max"), sd=("is_significant_deficiency", "max")))
    link["award_severity"] = np.select([link.mw, link.sd], SEVERITY[:2], default=SEVERITY[2])
    a = a.merge(link[["report_id", "award_reference", "award_severity"]],
                on=["report_id", "award_reference"], how="left")
    a["award_severity"] = a["award_severity"].fillna("No finding")

    pairs = (fr[["report_id", "reference_number", "award_reference"]]
             .merge(a[["report_id", "award_reference", "program"]].drop_duplicates(),
                    on=["report_id", "award_reference"], how="left"))
    pairs["program"] = pairs["program"].fillna("(not matched to a program)")
    pairs = (pairs.drop_duplicates(["report_id", "reference_number", "program"])
             .merge(uf[["report_id", "reference_number", "severity"]],
                    on=["report_id", "reference_number"], how="left"))
    n_unlinked = uf_scope.shape[0] - pairs[["report_id", "reference_number"]].drop_duplicates().shape[0]

    print("\nDrawing figures ...")
    fig_spending(a, scope, years, aud, last_complete, label, out / "fig1_spending_by_year_and_agency.png")
    fig_findings_by_year(uf_scope, scope, years, aud, last_complete, label,
                         out / "fig2_findings_by_year.png")
    fig_findings_by_program(pairs, label, out / "fig3_findings_by_program.png")
    overall = fig_dollars_by_program(a, label, out / "fig4_dollars_by_program_and_finding.png",
                                     out / "program_dollars_by_finding_status.csv")
    bench = None
    if nm.report_id.nunique() >= 50:
        bench = fig_benchmark(scope, nm, uf, last_complete, label,
                              out / "fig5_cuba_vs_new_mexico.png",
                              out / "cuba_vs_nm_table.csv")
    else:
        print("  (general.csv holds fewer than 50 New Mexico audits, so the Cuba vs NM chart is skipped; "
              "use the full FAC files to get it)")

    # Tables you can open in Excel and read line by line.
    per_audit = scope[["report_id", "audit_year", "auditee_name"]].copy()
    per_audit["federal_dollars"] = per_audit.report_id.map(a.groupby("report_id").amount.sum()).fillna(0)
    per_audit["findings"] = per_audit.report_id.map(uf_scope.groupby("report_id").size()).fillna(0).astype(int)
    per_audit["material_weakness_findings"] = per_audit.report_id.map(
        uf_scope[uf_scope.severity == "Material weakness"].groupby("report_id").size()).fillna(0).astype(int)
    per_audit.sort_values(["audit_year", "auditee_name"]).to_csv(out / "audits_in_scope.csv", index=False)
    progs = pairs.groupby(["report_id", "reference_number"]).program.agg("; ".join).rename("programs")
    ft = uf_scope.merge(progs, on=["report_id", "reference_number"], how="left")
    if "type_requirement" in f_rows:
        req = f_rows.groupby(["report_id", "reference_number"]).type_requirement.first()
        ft = ft.merge(req, on=["report_id", "reference_number"], how="left")
    ft.sort_values(["audit_year", "auditee_name", "reference_number"]).to_csv(
        out / "findings_in_scope.csv", index=False)

    # Plain-English numbers for the talk.
    n_aud, n_find = len(scope), len(uf_scope)
    n_aud_f = uf_scope.report_id.nunique()
    n_mw_aud = uf_scope[uf_scope.severity == "Material weakness"].report_id.nunique()
    print("\n--- Numbers for the presentation ---")
    print(f"{n_aud} audits in scope, {int(aud.index.min())}-{int(aud.index.max())}.")
    print(f"{n_find} findings (each counted once) in {n_aud_f} audits; "
          f"{n_mw_aud} audits reported a material weakness.")
    if n_find:
        yrs = sorted(int(y) for y in uf_scope.audit_year.unique())
        print(f"Audit years with findings: {yrs}")
    print(f"{n_unlinked} finding(s) not tied to a specific program.")
    print(f"{overall:.0%} of federal dollars were on awards with at least one finding.")
    if bench is not None:
        b = bench[bench.window == "Last 5 complete years"].set_index("who")
        print("Last 5 complete years - share of audits with a finding: "
              f"Cuba {b.loc['Cuba', 'share_audits_with_finding']:.0%} "
              f"(n={int(b.loc['Cuba', 'audits'])}) vs "
              f"NM {b.loc['New Mexico', 'share_audits_with_finding']:.0%} "
              f"(n={int(b.loc['New Mexico', 'audits'])}).")
    print(f"\nAll files are in: {out.resolve()}")


if __name__ == "__main__":
    main()

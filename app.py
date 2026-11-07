from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from pandas.errors import EmptyDataError, ParserError


st.set_page_config(
    page_title="ENG220 Group 11 | Financial Accountability",
    page_icon="📊",
    layout="wide",
)


# Synthetic values for testing the interface only.
def make_demo_data():
    return pd.DataFrame({
        "year": [
            2022, 2022, 2022,
            2023, 2023, 2023,
            2024, 2024, 2024,
        ],
        "category": [
            "Example A", "Example B", "Example C",
            "Example A", "Example B", "Example C",
            "Example A", "Example B", "Example C",
        ],
        "amount": [
            120000, 85000, 150000,
            135000, 95000, 140000,
            128000, 110000, 175000,
        ],
    })


def pending_section(title, description, planned_features):
    st.header(title)
    st.write(description)

    with st.container(border=True):
        st.info("Awaiting teammate-approved data.")

        st.subheader("Planned dashboard features")
        for feature in planned_features:
            st.write(f"• {feature}")

        st.caption(
            "This section does not load, modify, or classify "
            "teammates' current research files."
        )


demo = make_demo_data()


# Sidebar
with st.sidebar:
    st.title("ENG220 · Group 11")
    st.caption("Finance & Public Accountability")

    st.divider()

    demo_mode = st.toggle(
        "Enable interface demo",
        value=False,
        help=(
            "Show synthetic data to test charts and filters. "
            "These values are not research findings."
        ),
    )

    if demo_mode:
        st.subheader("Demo filters")

        selected_years = st.multiselect(
            "Years",
            options=sorted(demo["year"].unique().tolist()),
            default=sorted(demo["year"].unique().tolist()),
        )

        selected_categories = st.multiselect(
            "Categories",
            options=sorted(demo["category"].unique().tolist()),
            default=sorted(demo["category"].unique().tolist()),
        )
    else:
        selected_years = []
        selected_categories = []
        st.info("Audit filters are available in the Audit Findings tab.")

    st.divider()
    st.caption("Development build · Audit extraction preview")


# Header
st.title("Finance & Public Accountability")
st.write(
    "An interactive dashboard for exploring public financial "
    "records and documented accountability issues in New Mexico."
)

if demo_mode:
    st.warning(
        "DEMO MODE — All values in the Interface Demo tab are "
        "synthetic. They do not represent actual public finances "
        "or research findings."
    )
else:
    st.info(
        "The Audit Findings tab includes an extraction preview. "
        "Capital Appropriations and DOJ Releases are awaiting "
        "teammate-approved data for dashboard integration."
    )


overview, demo_tab, capital, doj, audits, methodology = st.tabs([
    "Overview",
    "Interface Demo",
    "Capital Appropriations",
    "DOJ Releases",
    "Audit Findings",
    "Data & Methodology",
])


# Overview
with overview:
    st.header("Project Overview")

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("Research question")
            st.write(
                "The group's approved research question "
                "will appear here."
            )

        with st.container(border=True):
            st.subheader("Project scope")
            st.write(
                "The study area, time period, and included "
                "records will be documented here."
            )

    with right:
        with st.container(border=True):
            st.subheader("Dashboard status")
            st.write("Layout: In development")
            st.write("Interactive interface: Available in demo mode")
            st.write("Research datasets: Awaiting handoff")

        with st.container(border=True):
            st.subheader("How to use this dashboard")
            st.write(
                "Choose a tab to explore a research area. "
                "The sidebar currently controls only the "
                "Interface Demo tab."
            )

    st.subheader("Research sections")

    st.dataframe(
        pd.DataFrame({
            "Section": [
                "Capital Appropriations",
                "DOJ Releases",
                "Audit Findings",
            ],
            "Dashboard integration": [
                "Awaiting approved financial output",
                "Awaiting approved release dataset",
                "Extraction preview implemented · Verification pending",
            ],
        }),
        hide_index=True,
        width="stretch",
    )


# Working interface demonstration
with demo_tab:
    st.header("Interface Demo")
    st.caption(
        "Synthetic development data only. "
        "Sidebar filters apply to every output in this tab."
    )

    if not demo_mode:
        st.info("Enable interface demo in the sidebar to test this section.")
    else:
        filtered = demo[
            demo["year"].isin(selected_years)
            & demo["category"].isin(selected_categories)
        ].copy()

        if filtered.empty:
            st.info(
                "No demo records match your selection. "
                "Select at least one year and category."
            )
        else:
            first, second, third = st.columns(3)

            first.metric(
                "Demo amount",
                f"${filtered['amount'].sum():,.0f}",
            )
            second.metric("Demo records", len(filtered))
            third.metric(
                "Years selected",
                filtered["year"].nunique(),
            )

            with st.container(border=True):
                chart_type = st.radio(
                    "Chart view",
                    ["Trend", "Category totals"],
                    horizontal=True,
                )

                if chart_type == "Trend":
                    fig = px.line(
                        filtered.sort_values("year"),
                        x="year",
                        y="amount",
                        color="category",
                        markers=True,
                        title="Synthetic amounts over time",
                        labels={
                            "year": "Example year",
                            "amount": "Synthetic amount ($)",
                            "category": "Example category",
                        },
                    )
                    fig.update_xaxes(dtick=1)
                else:
                    totals = (
                        filtered.groupby("category", as_index=False)
                        ["amount"].sum()
                    )

                    fig = px.bar(
                        totals,
                        x="category",
                        y="amount",
                        color="category",
                        title="Synthetic category totals",
                        labels={
                            "category": "Example category",
                            "amount": "Synthetic amount ($)",
                        },
                    )

                fig.update_yaxes(tickprefix="$")

                st.plotly_chart(fig, width="stretch")

            with st.expander("View and download demo records"):
                st.dataframe(
                    filtered,
                    hide_index=True,
                    width="stretch",
                )

                st.download_button(
                    "Download filtered demo CSV",
                    data=filtered.to_csv(index=False).encode("utf-8"),
                    file_name="SYNTHETIC_demo_data.csv",
                    mime="text/csv",
                )


# Research placeholders
with capital:
    pending_section(
        "Capital Appropriations",
        "Explore financial outputs supplied by the analysis team.",
        [
            "Filters based on the approved dataset",
            "Interactive financial comparisons",
            "Record details and source references",
            "Filtered table and CSV download",
        ],
    )

with doj:
    st.header("DOJ Releases")
    st.caption(
        "Browse the team's collected candidate press releases "
        "from the U.S. Department of Justice."
    )

    st.warning(
        "Research preview: keyword matches do not establish relevance "
        "to public corruption or prove misconduct. Releases may describe "
        "allegations, settlements, convictions, or other proceedings. "
        "Consult the original source for context."
    )

    doj_path = (
        Path(__file__).resolve().parent
        / "thomas_doj"
        / "nm_financial_review.csv"
    )

    if not doj_path.exists():
        st.info(
            "The DOJ dataset was not found at "
            "thomas_doj/nm_financial_review.csv."
        )
    else:
        try:
            releases = pd.read_csv(
                doj_path,
                encoding="utf-8-sig",
                dtype="string",
            )
        except (
            OSError,
            UnicodeError,
            EmptyDataError,
            ParserError,
        ) as exc:
            st.error("The DOJ dataset could not be read.")
            st.code(str(exc), language="text")
            releases = None

        if releases is not None:
            required_columns = {
                "release_id",
                "publication_date_utc",
                "title",
                "url",
                "matched_keywords",
                "article_text",
            }

            missing_columns = required_columns - set(releases.columns)

            if missing_columns:
                st.error(
                    "The DOJ dataset is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )

            elif releases.empty:
                st.info("The DOJ dataset contains no releases.")

            else:
                releases = releases.fillna("")

                for column in required_columns:
                    releases[column] = releases[column].str.strip()

                releases["publication_date"] = pd.to_datetime(
                    releases["publication_date_utc"],
                    errors="coerce",
                    utc=True,
                ).dt.date

                releases["_display_title"] = releases["title"].replace(
                    "",
                    "(Untitled release)",
                )

                st.caption(
                    "Counts below represent CSV records, not unique "
                    "cases, defendants, or verified findings."
                )

                search = st.text_input(
                    "Search titles and article text",
                    placeholder="Enter a name, organization, or phrase",
                    key="doj_search",
                ).strip()

                keyword_options = sorted({
                    keyword.strip()
                    for value in releases["matched_keywords"]
                    for keyword in value.split(",")
                    if keyword.strip()
                })

                selected_keywords = st.multiselect(
                    "Matched keywords — include any selected keyword",
                    options=keyword_options,
                    key="doj_keywords",
                )

                filtered_releases = releases.copy()

                if search:
                    search_mask = (
                        filtered_releases["title"].str.contains(
                            search,
                            case=False,
                            regex=False,
                            na=False,
                        )
                        | filtered_releases["article_text"].str.contains(
                            search,
                            case=False,
                            regex=False,
                            na=False,
                        )
                    )
                    filtered_releases = filtered_releases[search_mask]

                if selected_keywords:
                    keyword_mask = filtered_releases[
                        "matched_keywords"
                    ].apply(
                        lambda value: bool(
                            set(selected_keywords)
                            & {
                                keyword.strip()
                                for keyword in value.split(",")
                                if keyword.strip()
                            }
                        )
                    )
                    filtered_releases = filtered_releases[keyword_mask]

                valid_dates = releases["publication_date"].dropna()

                if not valid_dates.empty:
                    use_date_filter = st.checkbox(
                        "Filter by publication date",
                        value=False,
                        key="doj_use_date_filter",
                    )

                    if use_date_filter:
                        start_column, end_column = st.columns(2)

                        with start_column:
                            start_date = st.date_input(
                                "Start date",
                                value=valid_dates.min(),
                                min_value=valid_dates.min(),
                                max_value=valid_dates.max(),
                                key="doj_start_date",
                            )

                        with end_column:
                            end_date = st.date_input(
                                "End date",
                                value=valid_dates.max(),
                                min_value=valid_dates.min(),
                                max_value=valid_dates.max(),
                                key="doj_end_date",
                            )

                        if start_date > end_date:
                            st.warning(
                                "Start date must be on or before end date."
                            )
                            filtered_releases = (
                                filtered_releases.iloc[0:0]
                            )
                        else:
                            date_mask = filtered_releases[
                                "publication_date"
                            ].apply(
                                lambda value: (
                                    False
                                    if pd.isna(value)
                                    else start_date <= value <= end_date
                                )
                            )
                            filtered_releases = filtered_releases[
                                date_mask
                            ]

                        st.caption(
                            "Records with missing or invalid dates are "
                            "excluded while the date filter is enabled."
                        )
                else:
                    st.info(
                        "No valid publication dates were found. "
                        "Date filtering is unavailable."
                    )

                filtered_releases = filtered_releases.sort_values(
                    "publication_date",
                    ascending=False,
                    na_position="last",
                ).copy()

                total_column, filtered_column = st.columns(2)
                total_column.metric(
                    "Records in dataset",
                    len(releases),
                )
                filtered_column.metric(
                    "Matching records",
                    len(filtered_releases),
                )

                if filtered_releases.empty:
                    st.info("No releases match the selected filters.")

                else:
                    st.subheader("Matching releases")

                    st.dataframe(
                        filtered_releases[[
                            "publication_date_utc",
                            "title",
                            "matched_keywords",
                            "url",
                        ]],
                        column_config={
                            "publication_date_utc": "Publication date",
                            "title": "Release title",
                            "matched_keywords": "Matched keywords",
                            "url": st.column_config.LinkColumn(
                                "Original DOJ release",
                                display_text="Read source",
                            ),
                        },
                        hide_index=True,
                        width="stretch",
                    )

                    st.subheader("Release details")

                    detail_records = (
                        filtered_releases.reset_index(drop=True)
                    )

                    selection = st.selectbox(
                        "Choose a release",
                        options=list(range(len(detail_records))),
                        format_func=lambda index: (
                            f"{detail_records.iloc[index]['publication_date_utc']} "
                            f"— {detail_records.iloc[index]['_display_title']}"
                        ),
                    )

                    article = detail_records.iloc[selection]

                    st.subheader(article["_display_title"])
                    st.write(
                        "Publication date:",
                        article["publication_date_utc"]
                        or "Not provided",
                    )
                    st.write(
                        "Matched keywords:",
                        article["matched_keywords"]
                        or "Not provided",
                    )

                    source_url = article["url"]
                    if source_url.startswith(
                        ("https://www.justice.gov/", "https://justice.gov/")
                    ):
                        st.link_button(
                            "Open original DOJ release",
                            source_url,
                        )
                    else:
                        st.caption(
                            "A valid justice.gov source link "
                            "is not available for this record."
                        )

                    review_columns = {
                        "relevance": "Relevance",
                        "misconduct_category": "Misconduct category",
                        "case_stage": "Case stage",
                        "review_notes": "Review notes",
                    }

                    with st.expander("Team review fields"):
                        st.caption(
                            "Blank fields mean no value was supplied; "
                            "they do not indicate approval or verification."
                        )

                        for column, label in review_columns.items():
                            value = article.get(column, "")
                            st.write(
                                f"{label}: "
                                f"{value if value else 'Not provided'}"
                            )

                    with st.expander(
                        "Read collected article text",
                        expanded=True,
                    ):
                        st.text(
                            article["article_text"]
                            or "No article text was supplied."
                        )

                    export_columns = [
                        column
                        for column in releases.columns
                        if column not in {
                            "publication_date",
                            "_display_title",
                        }
                    ]

                    st.download_button(
                        "Download filtered DOJ records",
                        data=filtered_releases[
                            export_columns
                        ].to_csv(index=False).encode("utf-8-sig"),
                        file_name="filtered_doj_releases.csv",
                        mime="text/csv",
                        key="doj_download",
                    )

with audits:

    st.header("Audit Findings")
    st.caption("Village of Cuba special consulting report")

    data_path = (
        Path(__file__).resolve().parent
        / "data"
        / "processed"
        / "audit_findings_grouped.csv"
    )

    if not data_path.exists():
        st.info(
            "The audit preview dataset is missing: "
            "data/processed/audit_findings_grouped.csv. "
            "Check the required inputs and processing steps in "
            "scripts/prepare_audit_findings.py."
        )
    else:
        try:
            findings = pd.read_csv(data_path)
        except (OSError, UnicodeError, EmptyDataError, ParserError) as exc:
            st.error(
                "The audit dataset could not be read. "
                "Check that it is a valid, accessible CSV file."
            )
            st.code(str(exc), language="text")
            st.stop()

        required_columns = {
            "testing_group",
            "record_type",
            "label_candidate",
            "amount_usd",
            "transaction_count",
            "sample_size",
            "transaction_percent_calculated",
            "pdf_page",
            "review_status",
            "evidence",
        }

        missing_columns = required_columns - set(findings.columns)

        if missing_columns:
            st.error(
                "The audit dataset is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
            st.stop()

        if findings.empty:
            st.info("The audit dataset contains no records.")
            st.stop()

        text_columns = [
            "testing_group",
            "record_type",
            "label_candidate",
            "review_status",
            "evidence",
        ]

        for column in text_columns:
            findings[column] = (
                findings[column]
                .astype("string")
                .fillna("")
                .str.strip()
            )

        if findings[text_columns].eq("").any().any():
            st.error(
                "Some audit records are missing a testing group, "
                "record type, label, review status, or supporting evidence. "
                "Correct those records before displaying the preview."
            )
            st.stop()

        numeric_columns = [
            "amount_usd",
            "transaction_count",
            "sample_size",
            "transaction_percent_calculated",
            "pdf_page",
        ]

        for column in numeric_columns:
            findings[column] = pd.to_numeric(
                findings[column],
                errors="coerce",
            )

        invalid_numeric = (
            findings[numeric_columns].isna()
            | findings[numeric_columns].isin(
                [float("inf"), float("-inf")]
            )
        )

        if invalid_numeric.any().any():
            st.error(
                "Some audit records contain missing or invalid numbers. "
                "Check amounts, transaction counts, sample sizes, "
                "percentages, and PDF page references."
            )
            st.stop()

        integer_columns = [
            "transaction_count",
            "sample_size",
            "pdf_page",
        ]

        if (findings[integer_columns] % 1 != 0).any().any():
            st.error(
                "Transaction counts, sample sizes, and PDF page "
                "references must be whole numbers."
            )
            st.stop()

        invalid_ranges = (
            (findings["transaction_count"] < 0)
            | (findings["sample_size"] <= 0)
            | (
                findings["transaction_count"]
                > findings["sample_size"]
            )
            | (findings["pdf_page"] < 1)
            | ~findings["transaction_percent_calculated"].between(
                0, 100
            )
        )

        if invalid_ranges.any():
            st.error(
                "Some audit records have invalid counts, sample sizes, "
                "percentages, or PDF page references. "
                "Review the processed dataset."
            )
            st.stop()

        st.warning(
            "Extraction preview: records have not been independently "
            "verified. Categories may overlap. Amounts are not a "
            "total of proven losses or theft."
        )

        group = st.selectbox(
            "Testing group",
            sorted(findings["testing_group"].unique()),
        )

        selected = findings[
            findings["testing_group"] == group
        ].copy()

        show_supported = st.checkbox(
            "Include properly supported transactions",
            value=True,
        )

        if not show_supported:
            selected = selected[
                selected["record_type"] != "Supported transactions"
            ]

        sample_sizes = selected["sample_size"].unique()

        if len(sample_sizes) == 1:
            st.metric("Transactions in this tested sample", int(sample_sizes[0]))

        st.caption(
            "Percentages below are calculated from transaction counts, "
            "not from dollar amounts. Categories are not additive."
        )

        if selected.empty:
            st.info("No categories match the selected filters.")
        else:
            fig = px.bar(
                selected,
                x="transaction_percent_calculated",
                y="label_candidate",
                orientation="h",
                color="record_type",
                hover_data=[
                    "transaction_count",
                    "sample_size",
                    "amount_usd",
                    "pdf_page",
                ],
                labels={
                    "transaction_percent_calculated": "Sample transactions (%)",
                    "label_candidate": "Reported category",
                    "record_type": "Record type",
                    "amount_usd": "Reported amount ($)",
                },
                title=f"{group}: reported categories",
            )

            fig.update_xaxes(range=[0, 100], ticksuffix="%")
            fig.update_layout(
                height=max(400, len(selected) * 55),
                yaxis={"autorange": "reversed"},
            )

            st.plotly_chart(fig, width="stretch")

            st.subheader("Extracted records")

            st.dataframe(
                selected[[
                    "label_candidate",
                    "amount_usd",
                    "transaction_count",
                    "sample_size",
                    "transaction_percent_calculated",
                    "pdf_page",
                    "review_status",
                ]],
                hide_index=True,
            )

            with st.expander("Read supporting evidence"):
                for _, row in selected.iterrows():
                    st.write(
                        f"{row['label_candidate']} "
                        f"— PDF page {int(row['pdf_page'])}"
                    )
                    st.write(row["evidence"])
                    st.divider()

            st.download_button(
                "Download selected records",
                data=selected.to_csv(index=False).encode("utf-8-sig"),
                file_name="selected_audit_findings.csv",
                mime="text/csv",
            )


# Methodology placeholders
# Data sources and methodology
with methodology:
    st.header("Data & Methodology")

    with st.expander("Sources", expanded=True):
        st.subheader("Audit Findings")
        st.write(
            "The audit preview presents extracted records associated "
            "with a Village of Cuba special consulting report."
        )
        st.write("Dashboard dataset:")
        st.code(
            "data/processed/audit_findings_grouped.csv",
            language="text",
        )
        st.write(
            "The Audit Findings tab includes PDF page references "
            "and extracted supporting text for the displayed records."
        )
        st.info(
            "Source documentation is incomplete. Before publication, "
            "confirm the full report title, issuing organization, "
            "report date, period covered, original report URL, "
            "collection date, and responsible team member."
        )

        st.subheader("Capital Appropriations and DOJ Releases")
        st.write(
            "These dashboard sections are awaiting teammate-approved "
            "datasets. Their source documentation will be added "
            "during integration."
        )

    with st.expander("Data processing and review"):
        st.write(
            "The dashboard reads a processed CSV of extracted audit "
            "records and displays them by testing group. Users can "
            "include or exclude records labeled as supported transactions."
        )
        st.write(
            "The preview includes reported amounts, transaction counts, "
            "sample sizes, calculated percentages, PDF page references, "
            "and review-status fields."
        )
        st.warning(
            "Extracted records have not been independently verified. "
            "Check the original report before treating an extracted "
            "label, amount, count, or quotation as confirmed."
        )

    with st.expander("Definitions and interpretation"):
        st.write(
            "Transaction percentage = transaction count divided by "
            "sample size, multiplied by 100."
        )
        st.write(
            "These percentages describe transaction counts within "
            "the selected testing group, not percentages of dollars."
        )
        st.write(
            "Categories may overlap. Do not add category counts, "
            "percentages, or amounts together as if they represent "
            "distinct transactions."
        )
        st.write(
            "Reported amounts are not a total of proven losses or theft. "
            "Financial exceptions, audit findings, allegations, and "
            "adjudicated outcomes must remain distinct."
        )

    with st.expander("Interface demo"):
        st.write(
            "The Interface Demo tab uses synthetic values created "
            "only to test charts and filters. These values are not "
            "research findings and are separate from the audit dataset."
        )

    with st.expander("Data handoff"):
        st.write(
            "Team members should supply dashboard-ready data, column "
            "definitions, units, source references, and an explanation "
            "of their results before integration."
        )

    with st.expander("Limitations"):
        st.write(
            "The audit preview is not a comprehensive assessment of "
            "public finances or corruption in New Mexico."
        )
        st.write(
            "Extraction errors, incomplete source documentation, "
            "overlapping categories, and differences between tested "
            "samples limit interpretation."
        )
        st.write(
            "Capital Appropriations and DOJ Releases are not yet "
            "connected to this dashboard."
        )


st.divider()
st.caption(
    "ENG220 Group 11 · Development framework · "
    "Synthetic demo values are not research findings."
)
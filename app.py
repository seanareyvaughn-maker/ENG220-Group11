import pandas as pd
import plotly.express as px
import streamlit as st


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
        value=True,
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
        st.info("Real-data controls will be added after handoff.")

    st.divider()
    st.caption("Development build · Research data pending")


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
        "Framework preview — Research datasets have not been connected."
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
                "Awaiting structured findings",
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
    pending_section(
        "DOJ Releases",
        "Explore the team's approved press-release dataset.",
        [
            "Publication-date filters",
            "Title and text search",
            "Source links and article details",
            "Reviewed classifications when provided",
        ],
    )

with audits:
    pending_section(
        "Audit Findings",
        "Explore documented findings supplied by the research team.",
        [
            "Entity and year filters",
            "Finding descriptions",
            "Source documents and page references",
            "Visual summaries of approved classifications",
        ],
    )


# Methodology placeholders
with methodology:
    st.header("Data & Methodology")

    with st.expander("Sources", expanded=True):
        st.write(
            "Each connected dataset will list its original source, "
            "collection date, and responsible team member."
        )

    with st.expander("Data handoff"):
        st.write(
            "Team members supply dashboard-ready data, column "
            "definitions, units, and an explanation of their results. "
            "The dashboard presents those outputs."
        )

    with st.expander("Definitions and interpretation"):
        st.write(
            "Financial exceptions, audit findings, allegations, "
            "and adjudicated outcomes will be labeled separately."
        )

    with st.expander("Limitations"):
        st.write(
            "Coverage gaps, missing records, and dataset-specific "
            "limitations will be documented before publication."
        )


st.divider()
st.caption(
    "ENG220 Group 11 · Development framework · "
    "Synthetic demo values are not research findings."
)
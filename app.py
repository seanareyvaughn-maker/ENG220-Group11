import streamlit as st

st.set_page_config(
    page_title= "ENG220 Group 11 | Finacial ACcountability",
    page_icon="📊",
    layout="wide",
)

st.title("Finance & Public Accountability")
st.caption("ENG220 Group 11")

st.warning(
    "Dashboard under development. "
    "Cleaned research data has not been connected yet. "
)

with st.sidebar:
    st.header("Dashboard Controls")
    st.info("Data filters will appear here once data sets are connected.")

overview, finances, findings, methodology = st.tabs([
    "Overview",
    "Financial Explorer",
    "Audit Findings",
    "Data &Methodology"
])

with overview:
    st.header("Project Overview")
    st.write(
        "Explore public financial records and document audit "
        "findings through interactive visualizations."
    )

    st.subheader("Research Questions")
    st.info("Add the groups reasearch question here.")

    st.subheader("Project Status")
    st.write(
        "Data collection and cleanup are in progress. " 
        "the analyzed data is expeorted from MATLAB to CSV."
    )

with finances:
    st.header("Financial Explorer")
    st.write(
        "Interactive visualizations of public financial records."
    )

with findings:
    st.header("Documented Audit Findings")
    st.info(
        "Finding descriptions and supporting visualizations will be displayed here once the data is connected."
        "references will appear here."
    )

    st.caption(
        "Audit findings should not automatically be interpreted "
        "as proof of corruption."
    )

with methodology:
    st.header("Data & Methodology")

    st.subheader("Sources")
    st.write("Add source documents and references here.")

    st.subheader("Data Processing")
    st.write(
        "Document collection, cleanup, MATLAB analysis, "
        "and dashboard preperation here."
    )

    st.subheader("Limititations")
    st.write(
        "Document any missing records, coverage gaps, and "
        "interpretation limits here."
    )
# ERP Integration & Project Governance Dashboard
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="ERP Integration Dashboard",
    layout="wide"
)

st.title("ERP Integration & Project Governance Dashboard")

# -----------------------------
# Upload Excel
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Project Tracking Excel",
    type=["xlsx"]
)

# =========================================================
# MAIN APP LOGIC
# =========================================================
if uploaded_file:

    # -----------------------------
    # Read & Clean Data
    # -----------------------------
    df = pd.read_excel(uploaded_file)

    df = df.loc[:, ~df.columns.str.contains("Unnamed", na=False)]
    df.columns = df.columns.str.strip()

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Identify Project Status column
    status_col = [c for c in df.columns if c.lower() == "project status"][0]

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("Filters")

    def multi_filter(label, column):
        values = sorted(df[column].unique())
        return st.sidebar.multiselect(label, values, default=values)

    country = multi_filter("Country", "Country")
    status = multi_filter("Project Status", status_col)
    integration = multi_filter("Integration", "Integration")
    architecture = multi_filter("Architecture", "Architecture")
    spoc = multi_filter("SPOC from Webtel", "SPOC from Webtel")
    dev_owner = multi_filter("Dev Owner", "Dev Owner")

    # -----------------------------
    # Optional Filter Logic
    # -----------------------------
    def apply_filter(df, column, selected):
        if len(selected) == len(df[column].unique()):
            return True
        return df[column].isin(selected)

    filtered_df = df[
        (df["Country"].isin(country)) &
        (df[status_col].isin(status)) &
        apply_filter(df, "Integration", integration) &
        apply_filter(df, "Architecture", architecture) &
        apply_filter(df, "SPOC from Webtel", spoc) &
        apply_filter(df, "Dev Owner", dev_owner)
    ]

    # -----------------------------
    # KPI Calculations
    # -----------------------------
    total_projects = len(filtered_df)

    completed = filtered_df[filtered_df[status_col] == "Completed"]
    on_hold = filtered_df[filtered_df[status_col] == "On-Hold"]
    scrap = filtered_df[filtered_df[status_col] == "Scrap"]

    active = filtered_df[
        ~filtered_df[status_col].isin(["Completed", "On-Hold", "Scrap"])
    ]

    # -----------------------------
    # KPI Cards
    # -----------------------------
    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Projects", total_projects)
    k2.metric("Active Projects", len(active))
    k3.metric("Completed Projects", len(completed))
    k4.metric("On-Hold Projects", len(on_hold))
    k5.metric("Scrap Projects", len(scrap))

    st.markdown("---")

    # -----------------------------
    # Country-wise KPI Summary
    # -----------------------------
    st.subheader("Country-wise Project Summary")

    def classify_status(status):
        if status == "Completed":
            return "Completed"
        elif status == "On-Hold":
            return "On-Hold"
        elif status == "Scrap":
            return "Scrap"
        else:
            return "Active"

    filtered_df["Status Group"] = filtered_df[status_col].apply(classify_status)

    country_summary = (
        filtered_df
        .groupby(["Country", "Status Group"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["Active", "Completed", "On-Hold", "Scrap"]:
        if col not in country_summary.columns:
            country_summary[col] = 0

    country_summary["Total"] = (
        country_summary["Active"] +
        country_summary["Completed"] +
        country_summary["On-Hold"] +
        country_summary["Scrap"]
    )

    country_summary = country_summary[
        ["Country", "Total", "Active", "Completed", "On-Hold", "Scrap"]
    ]

    st.dataframe(
        country_summary.sort_values("Total", ascending=False),
        use_container_width=True
    )

    st.markdown("---")

    # -----------------------------
    # Project Insights (Enhanced Charts)
    # -----------------------------
    st.subheader("Project Insights")

    col1, col2 = st.columns(2)

    # Chart 1: Projects by Status
    with col1:
        st.markdown("### Projects by Status")
        fig, ax = plt.subplots()
        filtered_df[status_col].value_counts().plot(kind="bar", ax=ax)
        ax.set_xlabel("Status")
        ax.set_ylabel("Number of Projects")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # Chart 2: Projects by Integration
    with col2:
        st.markdown("### Projects by Integration")
        fig, ax = plt.subplots()
        filtered_df["Integration"].value_counts().sort_values().plot(kind="barh", ax=ax)
        ax.set_xlabel("Number of Projects")
        ax.set_ylabel("Integration Type")
        st.pyplot(fig)

    st.markdown("---")

    # Chart 3: Projects by SPOC
    st.markdown("### Projects by SPOC (Webtel)")
    fig, ax = plt.subplots(figsize=(8, 4))
    filtered_df["SPOC from Webtel"].value_counts().sort_values().plot(kind="barh", ax=ax)
    ax.set_xlabel("Number of Projects")
    ax.set_ylabel("SPOC Name")
    st.pyplot(fig)

    st.markdown("---")

    # -----------------------------
    # Project Details Table
    # -----------------------------
    st.subheader("Project Details")

    display_cols = [
        "Client name",
        "Country",
        status_col,
        "Integration",
        "Architecture",
        "SPOC from Webtel",
        "Dev Owner",
        "Project Start date",
        "Project End date",
        "Days",
        "Remarks"
    ]

    existing_cols = [c for c in display_cols if c in filtered_df.columns]

    st.dataframe(
        filtered_df[existing_cols],
        use_container_width=True
    )

    # -----------------------------
    # Export
    # -----------------------------
    st.download_button(
        "Download Filtered Data (CSV)",
        filtered_df.to_csv(index=False),
        "filtered_projects.csv",
        "text/csv"
    )

# =========================================================
# NO FILE UPLOADED
# =========================================================
else:
    st.info("Please upload the Excel file to view the dashboard.")

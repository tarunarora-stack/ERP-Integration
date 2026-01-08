import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="ERP Integration Dashboard", layout="wide")
st.title("ERP Integration & Project Governance Dashboard")

# -----------------------------
# Upload Excel
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Project Tracking Excel",
    type=["xlsx"]
)

# =====================================================
# MAIN LOGIC
# =====================================================
if uploaded_file:

    # -----------------------------
    # Read & Clean Data
    # -----------------------------
    df = pd.read_excel(uploaded_file)
    df = df.loc[:, ~df.columns.str.contains("Unnamed", na=False)]
    df.columns = df.columns.str.strip()

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

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
    # KPI Cards
    # -----------------------------
    total = len(filtered_df)
    completed = len(filtered_df[filtered_df[status_col] == "Completed"])
    on_hold = len(filtered_df[filtered_df[status_col] == "On-Hold"])
    scrap = len(filtered_df[filtered_df[status_col] == "Scrap"])
    active = total - (completed + on_hold + scrap)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", total)
    c2.metric("Active", active)
    c3.metric("Completed", completed)
    c4.metric("On-Hold", on_hold)
    c5.metric("Scrap", scrap)

    st.markdown("---")

    # -----------------------------
    # Country-wise Summary
    # -----------------------------
    st.subheader("Country-wise Project Summary")

    def classify_status(s):
        if s in ["Completed", "On-Hold", "Scrap"]:
            return s
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

    st.dataframe(
        country_summary[
            ["Country", "Total", "Active", "Completed", "On-Hold", "Scrap"]
        ].sort_values("Total", ascending=False),
        use_container_width=True
    )

    st.markdown("---")

    # -----------------------------
    # Charts
    # -----------------------------
    st.subheader("Project Insights")

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        filtered_df[status_col].value_counts().plot(kind="bar", ax=ax)
        ax.set_title("Projects by Status")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        filtered_df["Integration"].value_counts().sort_values().plot(kind="barh", ax=ax)
        ax.set_title("Projects by Integration")
        st.pyplot(fig)

    st.markdown("---")

    # -----------------------------
    # Excel-style SPOC TOTAL Chart
    # -----------------------------
    st.subheader("TOTAL – Projects by SPOC (Webtel)")

    spoc_counts = filtered_df["SPOC from Webtel"].value_counts()

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#3b3b3b")
    ax.set_facecolor("#3b3b3b")

    bars = ax.bar(spoc_counts.index, spoc_counts.values)

    ax.set_title("TOTAL", color="white", fontsize=18, pad=20)
    ax.tick_params(axis="x", colors="white", rotation=45)
    ax.tick_params(axis="y", colors="white")

    for spine in ax.spines.values():
        spine.set_visible(False)

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(int(bar.get_height())),
            ha="center",
            va="bottom",
            color="white",
            fontweight="bold"
        )

    st.pyplot(fig)

    st.markdown("---")

    # -----------------------------
    # Project Details
    # -----------------------------
    st.subheader("Project Details")

    st.dataframe(filtered_df, use_container_width=True)

    # -----------------------------
    # Export
    # -----------------------------
    st.download_button(
        "Download Filtered Data (CSV)",
        filtered_df.to_csv(index=False),
        "filtered_projects.csv",
        "text/csv"
    )

# =====================================================
# NO FILE UPLOADED
# =====================================================
else:
    st.info("Please upload the Excel file to view the dashboard.")

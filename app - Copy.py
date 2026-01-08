# ERP Integration & Project Governance Dashboard
# Run using: streamlit run app.py

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

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # -----------------------------
    # Data Cleanup & Normalization
    # -----------------------------
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains("Unnamed", na=False)]

    # Strip spaces from column names
    df.columns = df.columns.str.strip()

    # Normalize all text columns (VERY IMPORTANT)
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Identify Project Status column safely
    status_col = [c for c in df.columns if c.lower() == "project status"][0]

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("Filters")

    def multi_filter(label, column):
        values = sorted(df[column].unique())
        selected = st.sidebar.multiselect(
            label,
            values,
            default=values
        )
        return selected

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

    completed = filtered_df[
        filtered_df[status_col] == "Completed"
    ]

    on_hold = filtered_df[
        filtered_df[status_col] == "On-Hold"
    ]

    active = filtered_df[
        ~filtered_df[status_col].isin(["Completed", "Scrap"])
    ]

    avg_days = round(filtered_df["Days"].mean(), 2)

    # -----------------------------
    # KPI Display
    # -----------------------------
    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Projects", total_projects)
    k2.metric("Active Projects", len(active))
    k3.metric("Completed Projects", len(completed))
    k4.metric("On-Hold Projects", len(on_hold))
    k5.metric("Avg Duration (Days)", avg_days)

    st.markdown("---")



    # -----------------------------
    # Charts
    # -----------------------------
    st.subheader("Project Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Projects by Status")
        plt.figure()
        filtered_df[status_col].value_counts().plot(kind="bar")
        st.pyplot(plt)

    with col2:
        st.write("Projects by Integration")
        plt.figure()
        filtered_df["Integration"].value_counts().plot(kind="bar")
        st.pyplot(plt)

    col3, col4 = st.columns(2)

    with col3:
        st.write("Projects by SPOC (Webtel)")
        plt.figure()
        filtered_df["SPOC from Webtel"].value_counts().plot(kind="bar")
        st.pyplot(plt)

    with col4:
        st.write("Projects by Country")
        plt.figure()
        filtered_df["Country"].value_counts().plot(kind="bar")
        st.pyplot(plt)

    st.markdown("---")

    # -----------------------------
    # Project Detail Table
    # -----------------------------
    st.subheader("Project Detail View")

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
        label="Download Filtered Data (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_projects.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload the Excel file to view the dashboard.")

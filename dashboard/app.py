
import sys
import sqlite3
import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATABASE_PATH, PROCESSED_DATA_DIR


st.set_page_config(
    page_title="YottaFlex Collections Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("YottaFlex AI Delinquency & Collections")
st.caption("AI-assisted delinquency monitoring and collections analytics")


@st.cache_data
def load_data():
    with sqlite3.connect(DATABASE_PATH) as connection:
        loans = pd.read_sql_query("SELECT * FROM loans", connection)
        snapshots = pd.read_sql_query(
            "SELECT * FROM delinquency_snapshots", connection
        )
        cases = pd.read_sql_query(
            "SELECT * FROM collection_cases", connection
        )
        payments = pd.read_sql_query("SELECT * FROM payments", connection)
        promises = pd.read_sql_query(
            "SELECT * FROM promises_to_pay", connection
        )

    return loans, snapshots, cases, payments, promises


try:
    loans, snapshots, cases, payments, promises = load_data()

    # KPI calculations
    total_loans = len(loans)
    open_cases = len(cases[cases["case_status"] == "OPEN"])
    total_arrears = snapshots["arrears_amount"].sum()
    total_payments = payments["payment_amount"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Loans", f"{total_loans:,}")
    col2.metric("Open Collection Cases", f"{open_cases:,}")
    col3.metric("Total Arrears", f"₹{total_arrears:,.2f}")
    col4.metric("Total Payments", f"₹{total_payments:,.2f}")

    st.divider()

    # AI Edge Case Detection Performance
    st.subheader("AI Edge Case Detection Performance")

    report_path = PROCESSED_DATA_DIR / "evaluation_report.json"

    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as file:
            report = json.load(file)

        metric1, metric2, metric3, metric4 = st.columns(4)

        metric1.metric(
            "Precision",
            f"{report['precision'] * 100:.2f}%"
        )
        metric2.metric(
            "Recall",
            f"{report['recall'] * 100:.2f}%"
        )
        metric3.metric(
            "F1 Score",
            f"{report['f1_score'] * 100:.2f}%"
        )
        metric4.metric(
            "Detected Issues",
            f"{report['detected_cases']}/{report['expected_cases']}"
        )
    else:
        st.warning(
            "Evaluation report not found. Run the evaluation module."
        )

    st.divider()

    # Risk distribution
    st.subheader("Delinquency Risk Distribution")

    risk_counts = (
        snapshots["risk_category"]
        .value_counts()
        .rename_axis("Risk Category")
        .reset_index(name="Loan Count")
    )

    left, right = st.columns(2)

    with left:
        st.bar_chart(
            risk_counts.set_index("Risk Category")
        )

    with right:
        st.dataframe(
            risk_counts,
            width="stretch",
            hide_index=True,
        )

    st.divider()

    # Collection priority queue
    st.subheader("Collection Priority Queue")

    priority_queue = cases.merge(
        snapshots[
            [
                "loan_id",
                "days_past_due",
                "arrears_amount",
                "risk_category",
            ]
        ],
        on="loan_id",
        how="left",
    )

    priority_queue = priority_queue[
        priority_queue["case_status"] == "OPEN"
    ].sort_values(
        by="priority_score",
        ascending=False,
    )

    # Interactive filters
    st.subheader("Search and Filter Collection Cases")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        selected_risk = st.selectbox(
            "Filter by Risk Category",
            ["ALL"] + sorted(
                priority_queue["risk_category"].dropna().unique().tolist()
            ),
        )

    with filter_col2:
        search_text = st.text_input(
            "Search Loan ID or Case ID",
            placeholder="Example: LOAN-2026-000001",
        )

    filtered_queue = priority_queue.copy()

    if selected_risk != "ALL":
        filtered_queue = filtered_queue[
            filtered_queue["risk_category"] == selected_risk
        ]

    if search_text.strip():
        search_text = search_text.strip()
        filtered_queue = filtered_queue[
            filtered_queue["loan_id"].str.contains(
                search_text, case=False, na=False
            )
            | filtered_queue["case_id"].str.contains(
                search_text, case=False, na=False
            )
        ]

    st.write(f"Matching collection cases: {len(filtered_queue):,}")

    display_columns = [
        "case_id",
        "loan_id",
        "priority_score",
        "days_past_due",
        "arrears_amount",
        "risk_category",
        "case_status",
    ]

    st.dataframe(
        filtered_queue[display_columns].head(20),
        width="stretch",
        hide_index=True,
    )

    # Download filtered collection report
    csv_data = filtered_queue[display_columns].to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Collection Report (CSV)",
        data=csv_data,
        file_name="yottaflex_collection_report.csv",
        mime="text/csv",
    )

    st.divider()

    # Payment and promise summaries
    left, right = st.columns(2)

    with left:
        st.subheader("Payment Status")

        payment_summary = (
            payments["payment_status"]
            .value_counts()
            .rename_axis("Payment Status")
            .reset_index(name="Count")
        )

        st.bar_chart(
            payment_summary.set_index("Payment Status")
        )

    with right:
        st.subheader("Promise-to-Pay Status")

        promise_summary = (
            promises["promise_status"]
            .value_counts()
            .rename_axis("Promise Status")
            .reset_index(name="Count")
        )

        st.bar_chart(
            promise_summary.set_index("Promise Status")
        )

    st.caption(
        "Data source: Synthetic YottaFlex SQLite database. "
        "Priority scores are generated by the project pipeline."
    )

except Exception as error:
    st.error(f"Unable to load dashboard data: {error}")
    st.info("Check that the database has been generated successfully.")

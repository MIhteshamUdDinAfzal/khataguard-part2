"""
KhataGuard - AI-Powered Digital Khata

PART 1: UI & FRONTEND

This file contains only the dashboard UI.
All business calculations and database operations come from Part 2 Core.

Architecture:
Part 1 UI -> Part 2 Core -> SQLite
"""

import streamlit as st
import plotly.express as px

from backend.core import get_dashboard_summary


# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="KhataGuard",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# MOBILE-FRIENDLY CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 12px;
            padding: 14px;
        }

        .stButton button {
            border-radius: 10px;
            height: 3em;
            font-size: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

st.title("📒 KhataGuard")
st.caption("AI-Powered Digital Khata — bolo, aur khata khud ban jaye.")


# ---------------------------------------------------------------------------
# LOAD REAL DATA FROM PART 2 CORE
# ---------------------------------------------------------------------------

summary = get_dashboard_summary()

total_sale = float(summary["total_sales"])
total_paid = float(summary["total_received"])
total_outstanding = float(summary["total_outstanding"])

outstanding_customers = summary["outstanding_customers"]


# ---------------------------------------------------------------------------
# TOP METRICS
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Sale",
    f"Rs. {total_sale:,.0f}"
)

col2.metric(
    "Total Received",
    f"Rs. {total_paid:,.0f}"
)

col3.metric(
    "Total Outstanding",
    f"Rs. {total_outstanding:,.0f}"
)


st.divider()


# ---------------------------------------------------------------------------
# QUICK ACTIONS
# ---------------------------------------------------------------------------

st.subheader("Quick Actions")

a1, a2, a3 = st.columns(3)

with a1:
    if st.button(
        "➕ Customers",
        use_container_width=True
    ):
        st.switch_page("pages/1_Customers.py")

with a2:
    if st.button(
        "💰 Transactions",
        use_container_width=True
    ):
        st.switch_page("pages/2_Transactions.py")

with a3:
    if st.button(
        "📒 Ledger",
        use_container_width=True
    ):
        st.switch_page("pages/3_Ledger.py")


st.divider()


# ---------------------------------------------------------------------------
# TOP OUTSTANDING CUSTOMERS
# ---------------------------------------------------------------------------

st.subheader("Top Outstanding Customers")

if outstanding_customers:

    chart_data = []

    for customer in outstanding_customers:
        chart_data.append(
            {
                "customer": customer["name"],
                "outstanding": float(customer["outstanding"]),
            }
        )

    chart_data = sorted(
        chart_data,
        key=lambda x: x["outstanding"],
        reverse=True
    )[:5]

    if chart_data:

        fig_bar = px.bar(
            chart_data,
            x="customer",
            y="outstanding",
            text="outstanding",
            labels={
                "customer": "Customer",
                "outstanding": "Outstanding (Rs.)",
            },
        )

        fig_bar.update_traces(textposition="outside")

        fig_bar.update_layout(
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(
            fig_bar,
            use_container_width=True
        )

    else:
        st.info("Abhi koi outstanding customer nahi hai.")

else:
    st.info("Abhi koi outstanding customer nahi hai.")


# ---------------------------------------------------------------------------
# RECEIVED VS OUTSTANDING
# ---------------------------------------------------------------------------

st.subheader("Received vs Outstanding")

if total_paid > 0 or total_outstanding > 0:

    fig_pie = px.pie(
        names=["Received", "Outstanding"],
        values=[
            total_paid,
            total_outstanding,
        ],
        hole=0.5,
    )

    fig_pie.update_layout(
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

else:
    st.info("Abhi dashboard ke liye koi transaction data nahi hai.")


# ---------------------------------------------------------------------------
# ARCHITECTURE NOTE
# ---------------------------------------------------------------------------

st.info(
    "SQLite is the source of truth. "
    "Dashboard calculations Part 2 Core se aa rahi hain. "
    "UI khud business calculations nahi karti."
)

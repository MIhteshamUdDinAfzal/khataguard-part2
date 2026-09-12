import streamlit as st

from backend.core import (
    get_customers_for_ui,
    get_customer_statement,
)


st.set_page_config(
    page_title="Ledger - KhataGuard",
    page_icon="📒",
    layout="wide",
)


st.title("📒 Customer Ledger")

st.caption(
    "Kisi bhi customer ka poora hisaab — "
    "sale, paid, aur remaining balance."
)


# ============================================================
# Load Customers From Core
# ============================================================

try:
    customers = get_customers_for_ui()

except Exception as e:
    st.error(f"Could not load customers: {e}")
    customers = []


# ============================================================
# Customer Selection
# ============================================================

if not customers:

    st.info(
        "Abhi koi customer available nahi hai. "
        "Pehle Customers page se customer add karein."
    )

else:

    customer_options = {
        f"{customer['name']} (ID: {customer['id']})":
        customer["id"]
        for customer in customers
    }

    selected_customer = st.selectbox(
        "Customer Chunain",
        options=list(customer_options.keys())
    )

    customer_id = customer_options[selected_customer]

    st.divider()


    # ========================================================
    # Get Customer Statement From Core
    # ========================================================

    try:

        statement = get_customer_statement(
            customer_id
        )

        total_sale = statement["total_sale"]
        total_paid = statement["total_paid"]
        outstanding = statement["balance"]

    except Exception as e:

        st.error(
            f"Could not load customer ledger: {e}"
        )

        st.stop()


    # ========================================================
    # Financial Summary
    # ========================================================

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Total Sale",
            f"Rs. {total_sale:,.2f}"
        )

    with c2:
        st.metric(
            "Total Paid",
            f"Rs. {total_paid:,.2f}"
        )

    with c3:
        st.metric(
            "Outstanding",
            f"Rs. {outstanding:,.2f}"
        )


    st.divider()


    # ========================================================
    # Customer Information
    # ========================================================

    st.subheader(
        f"👤 {statement['customer_name']}"
    )

    if statement["phone"]:
        st.write(
            f"📞 Phone: {statement['phone']}"
        )

    st.write(
        f"🆔 Customer ID: {statement['customer_id']}"
    )


    # ========================================================
    # Transaction History
    # ========================================================

    st.subheader(
        f"📜 {statement['customer_name']} ki Transaction History"
    )

    ledger = statement["ledger"]

    if not ledger:

        st.info(
            "Is customer ki abhi koi transaction nahi hai."
        )

    else:

        history = []

        for transaction in ledger:

            history.append(
                {
                    "Date": transaction["transaction_date"],
                    "Type": transaction["type"].title(),
                    "Description": (
                        transaction["description"]
                        or "-"
                    ),
                    "Sale / Debit": (
                        f"Rs. {transaction['debit']:,.2f}"
                    ),
                    "Paid / Credit": (
                        f"Rs. {transaction['credit']:,.2f}"
                    ),
                    "Remaining": (
                        f"Rs. {transaction['balance']:,.2f}"
                    ),
                }
            )

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True,
        )


    # ========================================================
    # PDF Placeholder
    # ========================================================

    st.divider()

    st.button(
        "📄 PDF Statement Download "
        "(Part 5 mein active hoga)",
        disabled=True,
        use_container_width=True,
    )

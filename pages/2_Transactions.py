import streamlit as st

from backend.core import (
    list_customers,
    record_sale,
    record_payment,
)

from backend.ai.parser import parse_transaction


st.set_page_config(
    page_title="Transactions",
    page_icon="💰",
    layout="wide",
)


st.title("💰 Transactions")

st.write(
    "Add a sale or payment using Urdu, Roman Urdu, or English."
)


# -----------------------------------------
# AI Transaction Entry
# -----------------------------------------

st.subheader("🤖 AI Transaction Entry")

transaction_text = st.text_area(
    "Enter transaction",
    placeholder=(
        "Example: Ahmed ne 5000 ka saman liya "
        "aur 2000 de diye."
    ),
    height=120,
)


if st.button("Understand Transaction"):

    if not transaction_text.strip():

        st.warning("Please enter a transaction.")

    else:

        try:

            result = parse_transaction(
                transaction_text
            )

            st.session_state["ai_result"] = result

        except Exception as e:

            st.error(
                f"AI Error: {e}"
            )


# -----------------------------------------
# Show AI Result
# -----------------------------------------

if "ai_result" in st.session_state:

    result = st.session_state["ai_result"]

    st.subheader("AI Understanding")

    st.json(result)

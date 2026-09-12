import streamlit as st

from backend.core import (
    create_customer,
    find_customer_by_name,
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


# ============================================================
# AI Transaction Entry
# ============================================================

st.subheader("🤖 AI Transaction Entry")

transaction_text = st.text_area(
    "Enter transaction",
    placeholder=(
        "Example: Ahmed ne 5000 ka saman liya "
        "aur 2000 de diye."
    ),
    height=120,
)


# ============================================================
# Understand Transaction
# ============================================================

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

            st.error(f"AI Error: {e}")


# ============================================================
# AI Result
# ============================================================

if "ai_result" in st.session_state:

    result = st.session_state["ai_result"]

    st.subheader("🧠 AI Understanding")

    st.json(result)

    # --------------------------------------------------------
    # Check AI clarification
    # --------------------------------------------------------

    if result.get("needs_clarification"):

        st.warning(
            result.get(
                "question",
                "Please provide more information."
            )
        )

        st.info(
            "Transaction was NOT saved because "
            "more information is required."
        )

    else:

        customer_name = result.get("customer")
        sale_amount = result.get("sale", 0) or 0
        paid_amount = result.get("paid", 0) or 0

        # ----------------------------------------------------
        # Validate customer name
        # ----------------------------------------------------

        if not customer_name:

            st.error(
                "AI could not identify the customer."
            )

        else:

            try:

                customer = find_customer_by_name(
                    customer_name
                )

                customer_id = customer["id"]

                st.success(
                    f"Customer found: {customer['name']} "
                    f"(ID: {customer_id})"
                )

                # ------------------------------------------------
                # Show transaction information
                # ------------------------------------------------

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Sale",
                        f"Rs. {float(sale_amount):,.2f}"
                    )

                with col2:
                    st.metric(
                        "Paid",
                        f"Rs. {float(paid_amount):,.2f}"
                    )

                with col3:
                    st.metric(
                        "New Outstanding",
                        f"Rs. {float(sale_amount) - float(paid_amount):,.2f}"
                    )

                # ------------------------------------------------
                # Save transaction
                # ------------------------------------------------

                if st.button(
                    "💾 Save Transaction",
                    key="save_transaction"
                ):

                    try:

                        # Sale + payment
                        if float(sale_amount) > 0:

                            saved = record_sale(
                                customer_id=customer_id,
                                sale_amount=sale_amount,
                                paid_amount=paid_amount
                            )

                            st.success(
                                "Sale transaction saved successfully."
                            )

                            st.write(
                                f"Customer: "
                                f"{saved['customer_name']}"
                            )

                            st.write(
                                f"Sale: Rs. "
                                f"{saved['sale_amount']:,.2f}"
                            )

                            st.write(
                                f"Paid: Rs. "
                                f"{saved['paid_amount']:,.2f}"
                            )

                            st.write(
                                f"Outstanding: Rs. "
                                f"{saved['outstanding']:,.2f}"
                            )

                        # Payment only
                        elif float(paid_amount) > 0:

                            saved = record_payment(
                                customer_id=customer_id,
                                amount=paid_amount
                            )

                            st.success(
                                "Payment saved successfully."
                            )

                            st.write(
                                f"Customer: "
                                f"{saved['customer_name']}"
                            )

                            st.write(
                                f"Payment: Rs. "
                                f"{saved['payment_amount']:,.2f}"
                            )

                            st.write(
                                f"Outstanding: Rs. "
                                f"{saved['outstanding']:,.2f}"
                            )

                        else:

                            st.error(
                                "No sale or payment amount found."
                            )

                    except Exception as e:

                        st.error(
                            f"Could not save transaction: {e}"
                        )

            except ValueError as e:

                # ------------------------------------------------
                # Customer not found / duplicate customer
                # ------------------------------------------------

                st.warning(str(e))

                if "Customer not found" in str(e):

                    st.info(
                        f"Customer '{customer_name}' "
                        "does not exist."
                    )

                    st.write(
                        "Would you like to create this customer?"
                    )

                    if st.button(
                        "➕ Create Customer",
                        key="create_customer"
                    ):

                        try:

                            new_customer_id = create_customer(
                                name=customer_name
                            )

                            st.success(
                                f"Customer created successfully. "
                                f"Customer ID: {new_customer_id}"
                            )

                            st.info(
                                "Please click "
                                "'Save Transaction' again "
                                "after the customer is created."
                            )

                        except Exception as create_error:

                            st.error(
                                f"Could not create customer: "
                                f"{create_error}"
                            )

                else:

                    st.error(
                        "Please resolve the customer "
                        "identification problem before saving."
                    )

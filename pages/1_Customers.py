import streamlit as st

from backend.core import (
    create_customer,
    get_customers_for_ui,
)


st.set_page_config(
    page_title="Customers",
    page_icon="👥",
    layout="wide",
)


st.title("👥 Customers")
st.write("Manage your KhataGuard customers.")


# -----------------------------
# Add Customer
# -----------------------------

st.subheader("Add New Customer")

with st.form("add_customer_form"):
    name = st.text_input("Customer Name")
    phone = st.text_input("Phone Number")

    submitted = st.form_submit_button("Add Customer")

    if submitted:
        try:
            customer_id = create_customer(
                name=name,
                phone=phone
            )

            st.success(
                f"Customer added successfully. Customer ID: {customer_id}"
            )

        except ValueError as e:
            st.error(str(e))

        except Exception as e:
            st.error(f"Something went wrong: {e}")


st.divider()


# -----------------------------
# Customer Search
# -----------------------------

st.subheader("Customer List")

search = st.text_input(
    "Search customer",
    placeholder="Search by name or phone..."
)


try:
    customers = get_customers_for_ui(search=search)

    if not customers:
        st.info("No customers found.")

    else:
        for customer in customers:

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write("**Customer**")
                    st.write(customer["name"])

                with col2:
                    st.write("**Phone**")
                    st.write(customer["phone"] or "-")

                with col3:
                    st.write("**Total Sale**")
                    st.write(
                        f"Rs. {customer['total_sale']:,.2f}"
                    )

                with col4:
                    st.write("**Outstanding**")
                    st.write(
                        f"Rs. {customer['outstanding']:,.2f}"
                    )

except Exception as e:
    st.error(f"Could not load customers: {e}")

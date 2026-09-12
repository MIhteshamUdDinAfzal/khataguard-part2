from .database import get_connection


# ============================================================
# Allowed Transaction Types
# ============================================================

ALLOWED_TRANSACTION_TYPES = {"sale", "payment"}


# ============================================================
# Add Transaction
# ============================================================

def add_transaction(
    customer_id,
    transaction_type,
    amount,
    description=None,
    transaction_date=None
):
    """
    Add a sale or payment transaction for a customer.

    sale    = amount customer owes
    payment = amount customer has paid
    """

    # Validate transaction type
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValueError(
            "Transaction type must be 'sale' or 'payment'."
        )

    # Validate amount
    if amount is None:
        raise ValueError("Amount is required.")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a valid number.")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Check that customer exists
        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE id = ?
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            raise ValueError("Customer not found.")

        # Insert transaction
        if transaction_date:
            cursor.execute(
                """
                INSERT INTO transactions
                (
                    customer_id,
                    type,
                    amount,
                    description,
                    transaction_date
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    transaction_type,
                    amount,
                    description,
                    transaction_date
                )
            )
        else:
            cursor.execute(
                """
                INSERT INTO transactions
                (
                    customer_id,
                    type,
                    amount,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    customer_id,
                    transaction_type,
                    amount,
                    description
                )
            )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# Get One Transaction
# ============================================================

def get_transaction(transaction_id):
    """
    Get one transaction by ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                t.id,
                t.customer_id,
                c.name AS customer_name,
                t.type,
                t.amount,
                t.description,
                t.transaction_date,
                t.created_at
            FROM transactions t
            JOIN customers c
                ON t.customer_id = c.id
            WHERE t.id = ?
            """,
            (transaction_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# Get Customer Transactions
# ============================================================

def get_customer_transactions(customer_id):
    """
    Get all transactions belonging to one customer.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                customer_id,
                type,
                amount,
                description,
                transaction_date,
                created_at
            FROM transactions
            WHERE customer_id = ?
            ORDER BY transaction_date ASC, id ASC
            """,
            (customer_id,)
        )

        return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# Get All Transactions
# ============================================================

def get_all_transactions():
    """
    Get all transactions with customer names.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                t.id,
                t.customer_id,
                c.name AS customer_name,
                t.type,
                t.amount,
                t.description,
                t.transaction_date,
                t.created_at
            FROM transactions t
            JOIN customers c
                ON t.customer_id = c.id
            ORDER BY t.transaction_date DESC, t.id DESC
            """
        )

        return cursor.fetchall()

    finally:
        connection.close()


# ============================================================
# Delete Transaction
# ============================================================

def delete_transaction(transaction_id):
    """
    Delete a transaction by ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM transactions
            WHERE id = ?
            """,
            (transaction_id,)
        )

        if cursor.rowcount == 0:
            raise ValueError("Transaction not found.")

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def add_sale_and_payment(
    customer_id,
    sale_amount,
    paid_amount=0,
    description=None,
    transaction_date=None
):
    if sale_amount is None:
        raise ValueError("Sale amount is required.")

    try:
        sale_amount = float(sale_amount)
        paid_amount = float(paid_amount or 0)
    except (TypeError, ValueError):
        raise ValueError("Amounts must be valid numbers.")

    if sale_amount <= 0:
        raise ValueError("Sale amount must be greater than zero.")

    if paid_amount < 0:
        raise ValueError("Paid amount cannot be negative.")

    if paid_amount > sale_amount:
        raise ValueError(
            "Paid amount cannot be greater than sale amount."
        )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM customers
            WHERE id = ?
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            raise ValueError("Customer not found.")

        if transaction_date:
            cursor.execute(
                """
                INSERT INTO transactions
                (
                    customer_id,
                    type,
                    amount,
                    description,
                    transaction_date
                )
                VALUES (?, 'sale', ?, ?, ?)
                """,
                (
                    customer_id,
                    sale_amount,
                    description,
                    transaction_date
                )
            )
        else:
            cursor.execute(
                """
                INSERT INTO transactions
                (
                    customer_id,
                    type,
                    amount,
                    description
                )
                VALUES (?, 'sale', ?, ?)
                """,
                (
                    customer_id,
                    sale_amount,
                    description
                )
            )

        sale_transaction_id = cursor.lastrowid

        payment_transaction_id = None

        if paid_amount > 0:
            if transaction_date:
                cursor.execute(
                    """
                    INSERT INTO transactions
                    (
                        customer_id,
                        type,
                        amount,
                        description,
                        transaction_date
                    )
                    VALUES (?, 'payment', ?, ?, ?)
                    """,
                    (
                        customer_id,
                        paid_amount,
                        description,
                        transaction_date
                    )
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO transactions
                    (
                        customer_id,
                        type,
                        amount,
                        description
                    )
                    VALUES (?, 'payment', ?, ?)
                    """,
                    (
                        customer_id,
                        paid_amount,
                        description
                    )
                )

            payment_transaction_id = cursor.lastrowid

        connection.commit()

        return {
            "sale_transaction_id": sale_transaction_id,
            "payment_transaction_id": payment_transaction_id,
            "sale_amount": sale_amount,
            "paid_amount": paid_amount,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

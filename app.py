from datetime import datetime
from decimal import Decimal, InvalidOperation
import streamlit as st
import pandas as pd

from controllers import (
    AuthController,
    AccountController,
    TransactionController,
    TransferController,
    LoanController,
    OverDraftController,
    EmployeeController,
    ReportController,
)


st.set_page_config(page_title="Portsaid International Bank", page_icon="assets/PIB.jpg", layout="wide")

# Light theme (white + green) styling
st.markdown(
    """
    <style>
    :root {
      --primary-color: #0a8a3a;
      --secondary-background-color: #f8fff9;
    }
    .stApp {
      background-color: #ffffff;
    }
    div[data-testid="stSidebar"] {
      background-color: #f1fff3;
    }
    .stButton>button, .stDownloadButton>button {
      background-color: #0a8a3a !important;
      color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

auth_controller = AuthController()
account_controller = AccountController()
transaction_controller = TransactionController()
transfer_controller = TransferController()
loan_controller = LoanController()
overdraft_controller = OverDraftController()
employee_controller = EmployeeController()
report_controller = ReportController()


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    return f"{currency} {amount:,.2f}"


def require_session():
    if "session" not in st.session_state:
        st.stop()


def refresh_accounts():
    session = st.session_state.get("session")
    if session:
        accounts = account_controller.list_customer_accounts(session.customer.customer_id)
        st.session_state["session"] = session.__class__(
            role=session.role,
            customer=session.customer,
            employee=session.employee,
            accounts=accounts,
        )


def login_view():
    st.title("Login")
    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")
    if st.button("Sign in"):
        context = auth_controller.login(username, pin)
        if context:
            st.session_state["session"] = context
            who = context.customer.name if context.role == "customer" else context.employee.name
            st.success(f"Welcome back, {who} ({context.role})")
            st.rerun()
        else:
            st.error("Invalid credentials or inactive user.")


def account_overview():
    require_session()
    session = st.session_state["session"]
    st.subheader("Accounts")
    if not session.accounts:
        st.info("No accounts found.")
        return
    data = [
        {
            "Account": a.account_number,
            "Type": a.account_type,
            "Balance": float(a.balance),
            "Currency": a.currency,
            "Status": a.status,
            "Opened": a.date_opened.strftime("%Y-%m-%d"),
        }
        for a in session.accounts
    ]
    df = pd.DataFrame(data)
    st.table(df)


def transaction_history():
    require_session()
    session = st.session_state["session"]
    st.subheader("Transaction History")
    account_number = st.selectbox("Account", [a.account_number for a in session.accounts])
    col1, col2, col3 = st.columns(3)
    with col1:
        start = None
        if st.checkbox("Filter by start date", key="start-filter"):
            start = st.date_input("Start date")
    with col2:
        end = None
        if st.checkbox("Filter by end date", key="end-filter"):
            end = st.date_input("End date")
    with col3:
        txn_type = st.selectbox("Type", ["All", "DEPOSIT", "WITHDRAWAL", "TRANSFER_IN", "TRANSFER_OUT"])

    start_dt = datetime.combine(start, datetime.min.time()) if start else None
    end_dt = datetime.combine(end, datetime.max.time()) if end else None
    txns = transaction_controller.history(
        account_number=account_number,
        start_date=start_dt,
        end_date=end_dt,
        transaction_type=txn_type if txn_type != "All" else None,
    )
    if not txns:
        st.info("No transactions found for this filter.")
        return
    rows = [
        {
            "ID": t.transaction_id,
            "When": t.timestamp.strftime("%Y-%m-%d %H:%M"),
            "Type": t.transaction_type,
            "Amount": float(t.amount),
            "Balance After": float(t.balance_after),
            "Note": t.note or "",
            "Ref": t.reference_code or "",
        }
        for t in txns
    ]
    st.dataframe(pd.DataFrame(rows))


def cash_movement():
    require_session()
    session = st.session_state["session"]
    st.subheader("Deposit / Withdraw")
    account_number = st.selectbox("Account", [a.account_number for a in session.accounts])
    col1, col2 = st.columns(2)
    with col1:
        amount_str = st.text_input("Amount")
        action = st.selectbox("Action", ["Deposit", "Withdraw"])
        note = st.text_input("Note", value="")
    with col2:
        performer = st.text_input("Performed by", value=session.customer.name)
    if st.button("Submit"):
        try:
            amount = Decimal(amount_str)
            if action == "Deposit":
                transaction_controller.deposit(account_number, amount, performed_by=performer, note=note or None)
            else:
                transaction_controller.withdraw(account_number, amount, performed_by=performer, note=note or None)
            refresh_accounts()
            st.success(f"{action} completed.")
        except (InvalidOperation, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Operation failed: {exc}")


def transfer_view():
    require_session()
    session = st.session_state["session"]
    st.subheader("Transfer")
    accounts = [a.account_number for a in session.accounts]
    from_acct = st.selectbox("From", accounts)
    to_acct = st.text_input("To account number")
    amount_str = st.text_input("Amount to transfer")
    note = st.text_input("Note", value="")
    performer = st.text_input("Performed by", value=session.customer.name)
    if st.button("Send Transfer"):
        try:
            amount = Decimal(amount_str)
            transfer_controller.transfer(from_account=from_acct, to_account=to_acct, amount=amount, performed_by=performer, note=note or None)
            refresh_accounts()
            st.success("Transfer completed.")
        except (InvalidOperation, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Transfer failed: {exc}")


def loan_view():
    require_session()
    session = st.session_state["session"]
    st.subheader("Loans")
    account_number = st.selectbox("Account", [a.account_number for a in session.accounts])
    loans = loan_controller.list_loans(account_number)
    if loans:
        data = [
            {
                "Loan ID": l.loan_id,
                "Principal": float(l.principal),
                "Remaining": float(l.balance_remaining),
                "Rate": float(l.rate),
                "Term (months)": l.term_months,
                "Status": l.status,
                "Start": l.start_date.strftime("%Y-%m-%d"),
                "Next Due": l.next_due_date.strftime("%Y-%m-%d") if l.next_due_date else "",
            }
            for l in loans
        ]
        st.table(pd.DataFrame(data))
    else:
        st.info("No loans for this account.")

    st.markdown("---")
    st.write("Request a new loan")
    principal_str = st.text_input("Principal")
    rate_str = st.text_input("Rate (e.g., 4.5)")
    term = st.number_input("Term (months)", min_value=1, value=12)
    if st.button("Submit Loan Request"):
        try:
            principal = Decimal(principal_str)
            rate = Decimal(rate_str)
            loan_controller.request_loan(account_number, principal=principal, rate=rate, term_months=int(term))
            st.success("Loan request submitted.")
        except (InvalidOperation, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Loan request failed: {exc}")

def overdraft_view():
    require_session()
    session = st.session_state["session"]
    st.subheader("Overdraft Events")
    accounts = [a.account_number for a in session.accounts]
    if not accounts:
        st.info("No accounts.")
        return
    account_number = st.selectbox("Account", accounts)
    events = overdraft_controller.list_events(account_number)
    if not events:
        st.info("No overdraft events for this account.")
        return
    data = [
        {
            "When": e.occurred_at.strftime("%Y-%m-%d %H:%M"),
            "Amount": float(e.amount),
            "Balance": float(e.balance_after),
            "Note": e.note or "",
        }
        for e in events
    ]
    st.table(pd.DataFrame(data))


def employee_create_customer_view():
    st.subheader("Create Customer Profile")
    with st.form("create_customer"):
        username = st.text_input("Username")
        pin = st.text_input("PIN", type="password")
        name = st.text_input("Full name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        national_id = st.text_input("National ID")
        submitted = st.form_submit_button("Create")
    if submitted:
        try:
            customer = employee_controller.create_customer(
                username=username,
                pin=pin,
                name=name,
                email=email,
                phone=phone or None,
                address=address or None,
                national_id=national_id,
            )
            st.success(f"Customer created with id {customer.customer_id}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to create customer: {exc}")


def employee_cash_ops_view():
    st.subheader("Deposit / Withdraw (Employee)")
    account_number = st.text_input("Account number")
    amount_str = st.text_input("Amount")
    action = st.selectbox("Action", ["Deposit", "Withdraw"])
    note = st.text_input("Note", value="")
    performer = st.text_input("Performed by", value="employee")
    if st.button("Submit Cash Operation"):
        try:
            amount = Decimal(amount_str)
            if action == "Deposit":
                transaction_controller.deposit(account_number, amount, performed_by=performer, note=note or None)
            else:
                transaction_controller.withdraw(account_number, amount, performed_by=performer, note=note or None)
            st.success(f"{action} completed.")
        except (InvalidOperation, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Operation failed: {exc}")


def employee_review_loans_view():
    st.subheader("Review Loans")
    loans = employee_controller.list_all_loans()
    if not loans:
        st.info("No loans found.")
        return
    df = pd.DataFrame(
        [
            {
                "Loan ID": l.loan_id,
                "Account": l.account_number,
                "Principal": float(l.principal),
                "Remaining": float(l.balance_remaining),
                "Rate": float(l.rate),
                "Term": l.term_months,
                "Status": l.status,
                "Start": l.start_date.strftime("%Y-%m-%d"),
            }
            for l in loans
        ]
    )
    st.dataframe(df)
    st.markdown("Update loan status")
    loan_id = st.text_input("Loan ID to update")
    new_status = st.selectbox("Status", ["PENDING", "APPROVED", "REJECTED", "CLOSED"])
    if st.button("Update Loan Status"):
        try:
            employee_controller.update_loan_status(int(loan_id), new_status)
            st.success("Loan status updated.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to update loan: {exc}")


def employee_update_account_status_view():
    st.subheader("Update Account Status")
    account_number = st.text_input("Account number to update")
    new_status = st.selectbox("New status", ["ACTIVE", "FROZEN", "CLOSED"])
    if st.button("Apply Status Update"):
        try:
            employee_controller.update_account_status(account_number, new_status)
            st.success("Account status updated.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to update account: {exc}")


def employee_reports_view():
    st.subheader("Account Summary Report")
    account_number = st.text_input("Account number for summary")
    if st.button("Run Report"):
        if not account_number:
            st.error("Enter an account number")
            return
        summary = report_controller.account_summary(account_number)
        if not summary:
            st.info("No data for that account.")
            return
        st.table(
            pd.DataFrame(
                [
                    {
                        "Account": summary["account_number"],
                        "Customer": summary["customer_name"],
                        "Total In": float(summary["total_in"] or 0),
                        "Total Out": float(summary["total_out"] or 0),
                        "Overdraft Events": int(summary["overdraft_events"] or 0),
                    }
                ]
            )
        )


def employee_delete_ops_view():
    st.subheader("Delete Operations (guarded)")
    col1, col2 = st.columns(2)
    with col1:
        loan_id = st.text_input("Pending Loan ID to delete")
        if st.button("Delete Pending Loan"):
            try:
                employee_controller.delete_pending_loan(int(loan_id))
                st.success("Pending loan deleted (if status was PENDING).")
            except ValueError:
                st.error("Enter a valid loan ID.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to delete loan: {exc}")
    with col2:
        days = st.number_input("Delete overdraft events older than (days)", min_value=1, value=30)
        if st.button("Delete Old Overdraft Events"):
            try:
                employee_controller.delete_overdraft_events(int(days))
                st.success("Old overdraft events deleted.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to delete overdraft events: {exc}")


def main():
    st.title("Portsaid International Bank")
    if "session" in st.session_state:
        session = st.session_state["session"]
        name = session.customer.name if session.role == "customer" else session.employee.name
        st.info(f"Logged in as {name} ({session.role})")
        # Global logout control
        if st.button("Log out"):
            st.session_state.pop("session", None)
            st.rerun()

        st.sidebar.title("Navigation")

        if session.role == "customer":
            page = st.sidebar.radio(
                "Go to",
                ["Accounts", "Transactions", "Cash", "Transfers", "Loans", "Overdraft Events"],
            )
        else:
            page = st.sidebar.radio(
                "Go to",
                ["Create Customer", "Cash Ops", "Review Loans", "Update Account Status", "Reports", "Delete Ops"],
            )

        if st.sidebar.button("Logout"):
            st.session_state.pop("session", None)
            st.rerun()

        if session.role == "customer":
            if page == "Accounts":
                account_overview()
            elif page == "Transactions":
                transaction_history()
            elif page == "Cash":
                cash_movement()
            elif page == "Transfers":
                transfer_view()
            elif page == "Loans":
                loan_view()
            elif page == "Overdraft Events":
                overdraft_view()
        else:
            if page == "Create Customer":
                employee_create_customer_view()
            elif page == "Cash Ops":
                employee_cash_ops_view()
            elif page == "Review Loans":
                employee_review_loans_view()
            elif page == "Update Account Status":
                employee_update_account_status_view()
            elif page == "Reports":
                employee_reports_view()
            elif page == "Delete Ops":
                employee_delete_ops_view()
    else:
        login_view()


if __name__ == "__main__":
    main()

# Portsaid International Bank (Python + Streamlit + SQL Server)

Implements the walking skeleton (3-layer BCE style: UI → Controllers → DAOs/Entities → DB) with Streamlit as boundary, SQL Server persistence, and dataclass entities.

## Setup
- Python 3.11+ recommended.
- Install deps: `pip install -r requirements.txt`
- Create `.env` from `.env.example` and adjust credentials. If you use a named instance, set `DB_SERVER` to `localhost\\MSSQLSERVER01` (for your instance) and keep `DB_PORT=56539`; if you only have a host/port, use `localhost` with the port.
- Ensure the SQL Server ODBC driver in `.env` is installed (e.g., `ODBC Driver 17 for SQL Server`).

## Database
1) Create schema: run `scripts/create_tables.sql` (e.g., via `sqlcmd -S localhost,56539 -U <user> -P <pass> -i scripts/create_tables.sql` or `-S localhost\\MSSQLSERVER01,56539` if a named instance).
2) Seed demo data: `sqlcmd -S localhost,56539 -U <user> -P <pass> -i scripts/seed_data.sql` (same note for named instance).
   - Demo customers: `alice/1111`, `bob/2222`
   - Demo employees: `teller1/3333`, `officer1/4444`

## Run the app
```
streamlit run app.py
```

## Use-case map
- Auth/Context: `AuthController`, `SessionContext`
- Accounts/balances: `AccountController`
- History: `TransactionController.history`
- Deposits/withdrawals: `TransactionController.deposit/withdraw`
- Transfers: `TransferController.transfer`
- Loans: `LoanController.request_loan/list_loans`
- Overdraft events: `OverDraftController`
- Reports: `ReportController.account_summary` (aggregate + joins)
- Employee ops: `EmployeeController` (create customer, loan review/update, account status, delete ops)

## Assignment mapping (SQL + GUI)
- Queries with explanations: `docs/queries.md` (covers aggregates, subqueries, joins >2 tables, inserts/updates/deletes); runnable samples in `scripts/report_queries.sql`.
- Inserts: customer creation; transactions (deposit/withdraw); transfers; loan requests; overdraft events logging.
- Updates: account status; loan status; balances during cash ops/transfer.
- Deletes: employee "Delete Ops" page (pending loan delete; overdraft event cleanup).
- Selects: account lists/balances, transaction history with filters, loans, overdraft events, report summary.
- Report: employee "Reports" page shows account inflow/outflow and overdraft count (aggregate + joins).

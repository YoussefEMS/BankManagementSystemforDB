# Portsaid International Bank — SQL Reference with Context

This document explains each major SQL group in the project, what it does, and where it is used. Paths are relative to the repo root.

## 1) Schema Definition (`scripts/create_tables.sql`)
- **Purpose**: Defines the relational model used by all DAOs/UI flows.
- **Actions**:
  - Creates database `BankDB` if missing; drops existing tables in dependency-safe order.
  - Creates tables:
    - `Customers` (identity PK, unique `username`, `national_id`, contact info, status).
    - `Employees` (identity PK, unique `username`, role, status).
    - `Accounts` (PK `account_number`, FK to customer, type, balance, status, dates).
    - `Transactions` (identity PK, FK to account, type, amount, timestamp, balance_after, reference_code).
    - `Transfers` (identity PK, from/to account FKs, amount, status, note).
    - `Loans` (identity PK, FK to account, principal, remaining balance, rate, term, status, due date).
    - `OverDraftEvents` (identity PK, FK to account, amount, occurred_at, balance_after).
- **Used by**: Initial schema setup; required before seeding or running the app. All DAOs assume these tables exist and match the defined columns.

## 2) Bulk Seed Data (`scripts/seed_data.sql`)
- **Purpose**: Populate a rich dataset for demos/testing (100 customers, 300 accounts, 30 loans, transactions, transfers, overdrafts).
- **Actions**:
  - Clears all business tables (OverDraftEvents → Transfers → Transactions → Loans → Accounts → Customers → Employees).
  - Inserts 4 employees with roles (TELLER, LOAN_OFFICER, OPS).
  - Inserts 100 customers using a recursive CTE; generates usernames/pins/national IDs/contact info.
  - Inserts 300 accounts (3 per customer) with rotating account types and deterministic balances/dates.
  - Inserts 30 loans on the first 30 accounts with varying amounts, rates, and statuses.
  - Inserts transactions (2 per first 150 accounts) for seed deposits/withdrawals.
  - Inserts 50 transfers between sequential accounts and mirrors them into transaction logs (TRANSFER_IN/OUT).
  - Inserts 40 overdraft events tied to early accounts.
- **Used by**: Demo environment to exercise UI flows (history, transfers, loans, overdrafts, reports). Provides enough volume for aggregates and filters.

## 3) Reporting / Analytical Queries (`scripts/report_queries.sql`)
These queries answer business questions; each includes the SQL and the business perspective.

- **Account inflow/outflow and overdraft risk (aggregate + joins)**  
  _Business_: How much has this account received and paid out, and how risky is it (overdraft count)? Staff use it to assess account health.  
  ```sql
  SELECT
    a.account_number,
    c.name AS customer_name,
    SUM(CASE WHEN t.transaction_type IN ('DEPOSIT','TRANSFER_IN') THEN t.amount ELSE 0 END) AS total_in,
    SUM(CASE WHEN t.transaction_type IN ('WITHDRAWAL','TRANSFER_OUT') THEN t.amount ELSE 0 END) AS total_out,
    COUNT(DISTINCT o.event_id) AS overdraft_events
  FROM Accounts a
  JOIN Customers c ON c.customer_id = a.customer_id
  LEFT JOIN Transactions t ON t.account_number = a.account_number
  LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
  WHERE a.account_number = '10000001' -- replace parameter
  GROUP BY a.account_number, c.name;
  ```

- **Overdraft frequency by customer (aggregate + join)**  
  _Business_: Which customers trigger overdrafts, and how often? Highlights customers who may need outreach or account reviews.  
  ```sql
  SELECT c.customer_id, c.name, COUNT(o.event_id) AS overdraft_events
  FROM Customers c
  JOIN Accounts a ON a.customer_id = c.customer_id
  LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
  GROUP BY c.customer_id, c.name
  HAVING COUNT(o.event_id) > 0;
  ```

- **High-balance accounts (subquery)**  
  _Business_: Identify accounts above the bank-wide average balance to target premium servicing or retention efforts.  
  ```sql
  SELECT account_number, balance
  FROM Accounts
  WHERE balance > (SELECT AVG(balance) FROM Accounts);
  ```

- **Loans with above-average remaining balance (subquery)**  
  _Business_: Surface loans with unusually high remaining balances compared to all approved loans, to prioritize monitoring or follow-up.  
  ```sql
  SELECT loan_id, account_number, balance_remaining
  FROM Loans
  WHERE balance_remaining > (
    SELECT AVG(balance_remaining) FROM Loans WHERE status = 'APPROVED'
  );
  ```

- **Customer transaction history (join >2 tables)**  
  _Business_: Produce a statement-like view of all transactions for a customer across accounts, including the customer name for clarity in investigations or support.  
  ```sql
  SELECT t.transaction_id, t.timestamp, t.transaction_type, t.amount, a.account_number, c.name
  FROM Transactions t
  JOIN Accounts a ON a.account_number = t.account_number
  JOIN Customers c ON c.customer_id = a.customer_id
  WHERE a.customer_id = 1 -- replace parameter
  ORDER BY t.timestamp DESC;
  ```

- **Loan portfolio with ownership (join >2 tables)**  
  _Business_: Show each loan with its status, remaining balance, and who owns it (account + customer), for loan-ops dashboards.  
  ```sql
  SELECT l.loan_id, l.status, l.balance_remaining, a.account_number, c.name
  FROM Loans l
  JOIN Accounts a ON a.account_number = l.account_number
  JOIN Customers c ON c.customer_id = a.customer_id
  ORDER BY l.start_date DESC;
  ```

- **Housekeeping: close dormant frozen accounts (conditional UPDATE)**  
  _Business_: Automatically close accounts that are frozen and have zero balance to keep the ledger clean.  
  ```sql
  UPDATE Accounts SET status = 'CLOSED' WHERE status = 'FROZEN' AND balance = 0;
  ```

- **Housekeeping: delete pending loan applications (conditional DELETE)**  
  _Business_: Remove loan applications that never progressed (still PENDING), e.g., customer withdrawal or duplicates.  
  ```sql
  DELETE FROM Loans WHERE loan_id = 999 AND status = 'PENDING';
  ```

- **Housekeeping: purge old overdraft events (conditional DELETE with date)**  
  _Business_: Trim overdraft incident history older than the retention window to keep the table lean.  
  ```sql
  DELETE FROM OverDraftEvents WHERE occurred_at < DATEADD(day, -30, SYSUTCDATETIME());
  ```

## 4) Core Application Queries (DAOs)
These run via parameterized SQL in the DAOs. Each query is shown with placeholders and its business meaning.

### AuthDAO
- **Authenticate customer** — Verify active customer credentials to start a customer session.  
```sql
SELECT customer_id, name, national_id, email, phone, address, status, pin
FROM Customers
WHERE username = :username AND pin = :pin AND status = 'ACTIVE'
```
- **Create customer** — Register a new customer profile with contact and national ID, set to ACTIVE.  
```sql
INSERT INTO Customers (username, pin, name, email, phone, address, status, national_id)
VALUES (:username, :pin, :name, :email, :phone, :address, 'ACTIVE', :national_id)
```
- **List customers** — Retrieve all customers for employee/admin views.  
```sql
SELECT customer_id, name, national_id, email, phone, address, status, pin
FROM Customers
ORDER BY customer_id ASC
```

### EmployeeDAO
- **Authenticate employee** — Verify active employee credentials to start an employee session.  
```sql
SELECT employee_id, username, name, email, phone, role, status
FROM Employees
WHERE username = :username AND pin = :pin AND status = 'ACTIVE'
```

### AccountDAO
- **Accounts by customer** — Show all accounts owned by a customer (balances, types, status).  
```sql
SELECT account_number, customer_id, account_type, balance, currency, status, date_opened
FROM Accounts
WHERE customer_id = :customer_id
ORDER BY date_opened DESC
```
- **Single account** — Fetch one account to validate ownership/status/balance.  
```sql
SELECT account_number, customer_id, account_type, balance, currency, status, date_opened
FROM Accounts
WHERE account_number = :account_number
```
- **Update balance** — Apply balance changes after deposits/withdrawals/transfers.  
```sql
UPDATE Accounts
SET balance = :balance
WHERE account_number = :account_number
```
- **Update status** — Freeze/close/activate an account by staff.  
```sql
UPDATE Accounts
SET status = :status
WHERE account_number = :account_number
```
- **Create account** — Open a new account for a customer.  
```sql
INSERT INTO Accounts (account_number, customer_id, account_type, balance, currency, status, date_opened)
VALUES (:account_number, :customer_id, :account_type, :balance, :currency, :status, :date_opened)
```

### TransactionDAO
- **List history with filters** — Provide statement/history view with optional date/type filters.  
```sql
SELECT transaction_id, account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code
FROM Transactions
WHERE <dynamic filters: account_number = :account_number AND optional date/type clauses>
ORDER BY timestamp DESC
```
- **Insert transaction** — Log any cash/transfer operation with the resulting balance.  
```sql
INSERT INTO Transactions (account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code)
OUTPUT INSERTED.transaction_id
VALUES (:account_number, :transaction_type, :amount, SYSUTCDATETIME(), :performed_by, :note, :balance_after, :reference_code)
```
- **Get transaction by id** — Fetch a specific transaction (post-insert confirmation/audit).  
```sql
SELECT transaction_id, account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code
FROM Transactions
WHERE transaction_id = :transaction_id
```

### TransferDAO
- **List transfers for an account** — Show inbound and outbound transfers for an account.  
```sql
SELECT transfer_id, from_account, to_account, amount, timestamp, status, note
FROM Transfers
WHERE from_account = :acct OR to_account = :acct
ORDER BY timestamp DESC
```
- **Insert transfer** — Record a funds move between accounts.  
```sql
INSERT INTO Transfers (from_account, to_account, amount, timestamp, status, note)
OUTPUT INSERTED.transfer_id
VALUES (:from_account, :to_account, :amount, SYSUTCDATETIME(), :status, :note)
```

### LoanDAO
- **List loans by account** — Show loans tied to a specific account for the customer view.  
```sql
SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
FROM Loans
WHERE account_number = :account_number
ORDER BY start_date DESC
```
- **List all loans** — Portfolio view for employees to review/update.  
```sql
SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
FROM Loans
ORDER BY start_date DESC
```
- **Get loan by id** — Retrieve a specific loan for status changes or display.  
```sql
SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
FROM Loans
WHERE loan_id = :loan_id
```
- **Request/insert loan** — Create a loan request with initial status (e.g., PENDING).  
```sql
INSERT INTO Loans (account_number, principal, balance_remaining, rate, term_months, start_date, status)
OUTPUT INSERTED.loan_id
VALUES (:account_number, :principal, :principal, :rate, :term_months, :start_date, :status)
```
- **Update loan status** — Approve/reject/close a loan.  
```sql
UPDATE Loans SET status = :status WHERE loan_id = :loan_id
```
- **Delete pending loan** — Remove only loans that never advanced (PENDING).  
```sql
DELETE FROM Loans WHERE loan_id = :loan_id AND status = 'PENDING'
```

### OverDraftEventDAO
- **List overdraft events** — Show overdraft incidents for an account to inform the customer/staff.  
```sql
SELECT event_id, account_number, amount, occurred_at, note, balance_after
FROM OverDraftEvents
WHERE account_number = :account_number
ORDER BY occurred_at DESC
```
- **Insert overdraft event** — Log a blocked operation due to insufficient funds.  
```sql
INSERT INTO OverDraftEvents (account_number, amount, occurred_at, note, balance_after)
VALUES (:account_number, :amount, SYSUTCDATETIME(), :note, :balance_after)
```
- **Delete old overdraft events** — Purge events older than N days per retention.  
```sql
DELETE FROM OverDraftEvents
WHERE occurred_at < DATEADD(day, -:days, SYSUTCDATETIME())
```

### ReportingDAO
- **Account summary (inflow/outflow/overdrafts)** — Produce a concise health snapshot for an account.  
```sql
SELECT
  a.account_number,
  c.name AS customer_name,
  SUM(CASE WHEN t.transaction_type IN ('DEPOSIT','TRANSFER_IN') THEN t.amount ELSE 0 END) AS total_in,
  SUM(CASE WHEN t.transaction_type IN ('WITHDRAWAL','TRANSFER_OUT') THEN t.amount ELSE 0 END) AS total_out,
  COUNT(DISTINCT o.event_id) AS overdraft_events
FROM Accounts a
JOIN Customers c ON c.customer_id = a.customer_id
LEFT JOIN Transactions t ON t.account_number = a.account_number
LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
WHERE a.account_number = :account_number
GROUP BY a.account_number, c.name
```

## How They Map to the App
- Schema + seed must be run before the app: `scripts/create_tables.sql` then `scripts/seed_data.sql`.
- Controllers/UI invoke DAOs:
  - Auth/login → `AuthDAO` / `EmployeeDAO`
  - Accounts/balances → `AccountDAO`
  - History → `TransactionDAO.list_for_account`
  - Deposits/withdrawals → `TransactionDAO.add` + `AccountDAO.update_balance`
  - Transfers → `TransferDAO.add` + mirrored transaction inserts
  - Loans → `LoanDAO.request`, `LoanDAO.update_status`, `LoanDAO.delete_pending`
  - Overdrafts → `OverDraftEventDAO.add_event/delete_older_than_days`
  - Reports → `ReportingDAO.account_summary`

Use `scripts/report_queries.sql` as ready-made examples, and see DAO files for the exact parameterized SQL executed at runtime.

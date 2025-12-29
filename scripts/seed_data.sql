USE BankDB;
GO

-- Clear existing data
DELETE FROM OverDraftEvents;
DELETE FROM Transfers;
DELETE FROM Transactions;
DELETE FROM Loans;
DELETE FROM Accounts;
DELETE FROM Customers;
DELETE FROM Employees;
GO

-- Employees (a few sample staff)
INSERT INTO Employees (username, pin, name, email, phone, role, status) VALUES
('teller1', '3333', 'Teller One', 'teller1@example.com', '555-3333', 'TELLER', 'ACTIVE'),
('teller2', '3334', 'Teller Two', 'teller2@example.com', '555-3334', 'TELLER', 'ACTIVE'),
('officer1', '4444', 'Loan Officer', 'loan.officer@example.com', '555-4444', 'LOAN_OFFICER', 'ACTIVE'),
('ops1', '5555', 'Ops Staff', 'ops@example.com', '555-5555', 'OPS', 'ACTIVE');

-- 100 Customers
;WITH nums AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM nums WHERE n < 100
)
INSERT INTO Customers (username, pin, name, email, phone, address, national_id, status)
SELECT
    CONCAT('cust', n) AS username,
    RIGHT(CONCAT('0000', n), 4) AS pin,
    CONCAT('Customer ', n) AS name,
    CONCAT('customer', n, '@example.com') AS email,
    CONCAT('555-', RIGHT(CONCAT('0000', n), 4)) AS phone,
    CONCAT(n, ' Main Street, City') AS address,
    CONCAT('NATL-', RIGHT(CONCAT('000000', n), 6)) AS national_id,
    'ACTIVE' AS status
FROM nums
OPTION (MAXRECURSION 0);

-- 300 Accounts (3 per customer, types rotated)
;WITH cust AS (
    SELECT customer_id FROM Customers
),
acct_types AS (
    SELECT 'CHECKING' AS acct_type
    UNION ALL SELECT 'SAVINGS'
    UNION ALL SELECT 'FIXED'
),
acct_rows AS (
    SELECT TOP 300
        ROW_NUMBER() OVER (ORDER BY c.customer_id, a.acct_type) AS rn,
        c.customer_id,
        a.acct_type
    FROM cust c
    CROSS JOIN acct_types a
    ORDER BY c.customer_id, a.acct_type
)
INSERT INTO Accounts (account_number, customer_id, account_type, balance, currency, status, date_opened)
SELECT
    CONCAT('1', RIGHT(CONCAT('0000000', rn), 7)) AS account_number,
    customer_id,
    acct_type,
    CAST(ROUND(500 + rn * 17.35, 2) AS DECIMAL(18,2)) AS balance,
    'USD' AS currency,
    'ACTIVE' AS status,
    DATEADD(day, - (rn % 365), SYSUTCDATETIME()) AS date_opened
FROM acct_rows;

-- 30 Loans on first 30 accounts
;WITH top_accounts AS (
    SELECT TOP 30 account_number, ROW_NUMBER() OVER (ORDER BY account_number) AS rn
    FROM Accounts
    ORDER BY account_number
)
INSERT INTO Loans (account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date)
SELECT
    account_number,
    CAST(2000 + rn * 100 AS DECIMAL(18,2)) AS principal,
    CAST(2000 + rn * 100 - 50 AS DECIMAL(18,2)) AS balance_remaining,
    CAST(3.5 + (rn % 5) * 0.5 AS DECIMAL(5,2)) AS rate,
    12 + (rn % 4) * 6 AS term_months,
    DATEADD(day, - (rn * 5), SYSUTCDATETIME()) AS start_date,
    CASE WHEN rn % 3 = 0 THEN 'PENDING' WHEN rn % 3 = 1 THEN 'APPROVED' ELSE 'CLOSED' END AS status,
    DATEADD(day, 20, SYSUTCDATETIME()) AS next_due_date
FROM top_accounts;

-- Transactions: 2 per first 150 accounts
;WITH tx_accts AS (
    SELECT TOP 150 account_number, ROW_NUMBER() OVER (ORDER BY account_number) AS rn FROM Accounts ORDER BY account_number
)
INSERT INTO Transactions (account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code)
SELECT
    account_number,
    CASE WHEN rn % 2 = 0 THEN 'DEPOSIT' ELSE 'WITHDRAWAL' END AS transaction_type,
    CAST(100 + rn * 3 AS DECIMAL(18,2)) AS amount,
    DATEADD(day, - (rn % 30), SYSUTCDATETIME()) AS timestamp,
    'system' AS performed_by,
    CASE WHEN rn % 2 = 0 THEN 'Seed deposit' ELSE 'Seed withdrawal' END AS note,
    CAST(1000 + rn * 10 AS DECIMAL(18,2)) AS balance_after,
    NULL AS reference_code
FROM tx_accts
UNION ALL
SELECT
    account_number,
    'DEPOSIT',
    CAST(50 + rn * 2 AS DECIMAL(18,2)),
    DATEADD(day, - (rn % 15), SYSUTCDATETIME()),
    'system',
    'Seed deposit 2',
    CAST(1100 + rn * 9 AS DECIMAL(18,2)),
    NULL
FROM tx_accts;

-- Transfers: 50 sample transfers between sequential accounts
;WITH xfers AS (
    SELECT TOP 50
        a1.account_number AS from_account,
        a2.account_number AS to_account,
        ROW_NUMBER() OVER (ORDER BY a1.account_number) AS rn
    FROM Accounts a1
    JOIN Accounts a2 ON a2.account_number > a1.account_number
    ORDER BY a1.account_number, a2.account_number
)
INSERT INTO Transfers (from_account, to_account, amount, timestamp, status, note)
SELECT
    from_account,
    to_account,
    CAST(25 + rn * 5 AS DECIMAL(18,2)) AS amount,
    DATEADD(day, - (rn % 20), SYSUTCDATETIME()) AS timestamp,
    'COMPLETED' AS status,
    'Seed transfer'
FROM xfers;

-- Mirror transfers into transactions
INSERT INTO Transactions (account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code)
SELECT
    from_account,
    'TRANSFER_OUT',
    amount,
    timestamp,
    'seed_transfer',
    note,
    CAST(900 + rn * 8 AS DECIMAL(18,2)),
    CAST(rn AS NVARCHAR(20))
FROM xfers
UNION ALL
SELECT
    to_account,
    'TRANSFER_IN',
    amount,
    timestamp,
    'seed_transfer',
    note,
    CAST(950 + rn * 8 AS DECIMAL(18,2)),
    CAST(rn AS NVARCHAR(20))
FROM xfers;

-- Overdraft events: 40 events tied to early accounts
;WITH ods AS (
    SELECT TOP 40 account_number, ROW_NUMBER() OVER (ORDER BY account_number) AS rn FROM Accounts ORDER BY account_number
)
INSERT INTO OverDraftEvents (account_number, amount, occurred_at, note, balance_after)
SELECT
    account_number,
    CAST(20 + rn * 1.5 AS DECIMAL(18,2)),
    DATEADD(day, - (rn % 10), SYSUTCDATETIME()),
    'Seed overdraft event',
    CAST(100 - rn * 1.1 AS DECIMAL(18,2))
FROM ods;
GO

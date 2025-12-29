-- Aggregate inflow/outflow and overdraft count per account
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
WHERE a.account_number = '10000001' -- replace with parameter/account input
GROUP BY a.account_number, c.name;

-- Overdraft counts per customer
SELECT c.customer_id, c.name, COUNT(o.event_id) AS overdraft_events
FROM Customers c
JOIN Accounts a ON a.customer_id = c.customer_id
LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
GROUP BY c.customer_id, c.name
HAVING COUNT(o.event_id) > 0;

-- Accounts above average balance
SELECT account_number, balance
FROM Accounts
WHERE balance > (SELECT AVG(balance) FROM Accounts);

-- Loans with remaining balance above average approved
SELECT loan_id, account_number, balance_remaining
FROM Loans
WHERE balance_remaining > (
  SELECT AVG(balance_remaining) FROM Loans WHERE status = 'APPROVED'
);

-- Transaction history with customer name
SELECT t.transaction_id, t.timestamp, t.transaction_type, t.amount, a.account_number, c.name
FROM Transactions t
JOIN Accounts a ON a.account_number = t.account_number
JOIN Customers c ON c.customer_id = a.customer_id
WHERE a.customer_id = 1 -- replace with parameter
ORDER BY t.timestamp DESC;

-- Loan list with customer and account
SELECT l.loan_id, l.status, l.balance_remaining, a.account_number, c.name
FROM Loans l
JOIN Accounts a ON a.account_number = l.account_number
JOIN Customers c ON c.customer_id = a.customer_id
ORDER BY l.start_date DESC;

-- Update example (condition)
UPDATE Accounts SET status = 'CLOSED' WHERE status = 'FROZEN' AND balance = 0;

-- Delete pending loan
DELETE FROM Loans WHERE loan_id = 999 AND status = 'PENDING';

-- Delete overdraft events older than 30 days
DELETE FROM OverDraftEvents WHERE occurred_at < DATEADD(day, -30, SYSUTCDATETIME());

# Required SQL Queries (with explanations)

This file lists non-trivial, parameterized SQL statements used or ready to use in the app. They cover aggregates, subqueries, joins (>2 relations), and DML with conditions.

1) Aggregate: total inflow/outflow per account with overdraft count (joins 3+ tables)
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
GROUP BY a.account_number, c.name;
```
Explains inflow/outflow and overdraft frequency for an account.

2) Aggregate: overdraft counts per customer
```sql
SELECT c.customer_id, c.name, COUNT(o.event_id) AS overdraft_events
FROM Customers c
JOIN Accounts a ON a.customer_id = c.customer_id
LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
GROUP BY c.customer_id, c.name
HAVING COUNT(o.event_id) > 0;
```
Shows which customers triggered overdrafts (aggregate + join).

3) Subquery: accounts above average balance (overall)
```sql
SELECT account_number, balance
FROM Accounts
WHERE balance > (SELECT AVG(balance) FROM Accounts);
```

4) Subquery: loans whose remaining balance exceeds the average remaining balance of approved loans
```sql
SELECT loan_id, account_number, balance_remaining
FROM Loans
WHERE balance_remaining > (
  SELECT AVG(balance_remaining) FROM Loans WHERE status = 'APPROVED'
);
```

5) Join >2 tables: detailed transaction history with customer name
```sql
SELECT t.transaction_id, t.timestamp, t.transaction_type, t.amount, a.account_number, c.name
FROM Transactions t
JOIN Accounts a ON a.account_number = t.account_number
JOIN Customers c ON c.customer_id = a.customer_id
WHERE a.customer_id = :customer_id
ORDER BY t.timestamp DESC;
```

6) Join >2 tables: loan list with customer and account
```sql
SELECT l.loan_id, l.status, l.balance_remaining, a.account_number, c.name
FROM Loans l
JOIN Accounts a ON a.account_number = l.account_number
JOIN Customers c ON c.customer_id = a.customer_id
ORDER BY l.start_date DESC;
```

7) Update with condition: close inactive accounts
```sql
UPDATE Accounts SET status = 'CLOSED' WHERE status = 'FROZEN' AND balance = 0;
```

8) Delete with condition: delete pending loan
```sql
DELETE FROM Loans WHERE loan_id = :loan_id AND status = 'PENDING';
```

9) Delete with condition: delete overdraft events older than N days
```sql
DELETE FROM OverDraftEvents WHERE occurred_at < DATEADD(day, -@days, SYSUTCDATETIME());
```

10) Insert (new customer)
```sql
INSERT INTO Customers (username, pin, name, email, phone, address, national_id, status)
VALUES (:username, :pin, :name, :email, :phone, :address, :national_id, 'ACTIVE');
```

11) Insert (transaction log)
```sql
INSERT INTO Transactions (account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code)
VALUES (:account_number, :type, :amount, SYSUTCDATETIME(), :by, :note, :balance_after, :ref);
```

12) Select with filters: transaction history by date/type
```sql
SELECT transaction_id, account_number, transaction_type, amount, timestamp, note
FROM Transactions
WHERE account_number = :account
  AND (:start IS NULL OR timestamp >= :start)
  AND (:end IS NULL OR timestamp <= :end)
  AND (:type IS NULL OR transaction_type = :type)
ORDER BY timestamp DESC;
```

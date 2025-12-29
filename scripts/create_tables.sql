-- Create database objects for the Portsaid International Bank
IF DB_ID('BankDB') IS NULL
BEGIN
    PRINT 'Creating database BankDB';
    CREATE DATABASE BankDB;
END
GO

USE BankDB;
GO

IF OBJECT_ID('dbo.Transactions', 'U') IS NOT NULL DROP TABLE dbo.Transactions;
IF OBJECT_ID('dbo.Transfers', 'U') IS NOT NULL DROP TABLE dbo.Transfers;
IF OBJECT_ID('dbo.Loans', 'U') IS NOT NULL DROP TABLE dbo.Loans;
IF OBJECT_ID('dbo.OverDraftEvents', 'U') IS NOT NULL DROP TABLE dbo.OverDraftEvents;
IF OBJECT_ID('dbo.Accounts', 'U') IS NOT NULL DROP TABLE dbo.Accounts;
IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL DROP TABLE dbo.Customers;
IF OBJECT_ID('dbo.Employees', 'U') IS NOT NULL DROP TABLE dbo.Employees;
GO

CREATE TABLE Customers (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) NOT NULL UNIQUE,
    pin NVARCHAR(20) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    phone NVARCHAR(30) NULL,
    address NVARCHAR(255) NULL,
    national_id NVARCHAR(50) NOT NULL UNIQUE,
    status NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE Employees (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) NOT NULL UNIQUE,
    pin NVARCHAR(20) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    phone NVARCHAR(30) NULL,
    role NVARCHAR(30) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE Accounts (
    account_number NVARCHAR(20) NOT NULL PRIMARY KEY,
    customer_id INT NOT NULL FOREIGN KEY REFERENCES Customers(customer_id),
    account_type NVARCHAR(20) NOT NULL,
    balance DECIMAL(18,2) NOT NULL,
    currency NVARCHAR(3) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    date_opened DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE Transactions (
    transaction_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    account_number NVARCHAR(20) NOT NULL FOREIGN KEY REFERENCES Accounts(account_number),
    transaction_type NVARCHAR(20) NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    timestamp DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    performed_by NVARCHAR(100) NOT NULL,
    note NVARCHAR(255) NULL,
    balance_after DECIMAL(18,2) NOT NULL,
    reference_code NVARCHAR(50) NULL
);

CREATE TABLE Transfers (
    transfer_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    from_account NVARCHAR(20) NOT NULL FOREIGN KEY REFERENCES Accounts(account_number),
    to_account NVARCHAR(20) NOT NULL FOREIGN KEY REFERENCES Accounts(account_number),
    amount DECIMAL(18,2) NOT NULL,
    timestamp DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    status NVARCHAR(20) NOT NULL,
    note NVARCHAR(255) NULL
);

CREATE TABLE Loans (
    loan_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    account_number NVARCHAR(20) NOT NULL FOREIGN KEY REFERENCES Accounts(account_number),
    principal DECIMAL(18,2) NOT NULL,
    balance_remaining DECIMAL(18,2) NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    term_months INT NOT NULL,
    start_date DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    status NVARCHAR(20) NOT NULL,
    next_due_date DATETIME2 NULL
);

CREATE TABLE OverDraftEvents (
    event_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    account_number NVARCHAR(20) NOT NULL FOREIGN KEY REFERENCES Accounts(account_number),
    amount DECIMAL(18,2) NOT NULL,
    occurred_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    note NVARCHAR(255) NULL,
    balance_after DECIMAL(18,2) NOT NULL
);

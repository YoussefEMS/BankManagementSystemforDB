# Portsaid International Bank (Python + Streamlit + SQL Server)

Streamlit banking demo covering authentication, balances, history, transfers, loans, overdraft events, reporting, and employee operations. The code follows a 3-layer BCE-style layout: UI -> Controllers -> DAOs/Entities -> DB (see `WALKING_SKELETON.md`).

## Prerequisites
- Python 3.11+
- SQL Server reachable from your machine and the `sqlcmd` CLI
- ODBC driver for SQL Server (for example, `ODBC Driver 17 for SQL Server`)

## Setup
1) Install dependencies (virtualenv optional):  
`pip install -r requirements.txt`

2) Create `.env` in the repo root:
```env
DB_SERVER=localhost\\MSSQLSERVER01   # or localhost
DB_PORT=56539                        # or your port
DB_NAME=BankDB
DB_USER=<username>
DB_PASSWORD=<password>
DB_DRIVER=ODBC Driver 17 for SQL Server
POOL_MAX_SIZE=10
POOL_MIN_IDLE=2
POOL_IDLE_TIMEOUT_MS=300000
POOL_MAX_LIFETIME_MS=1800000
POOL_CONNECTION_TIMEOUT_MS=10000
```
If you use a named instance, keep the double backslash in `DB_SERVER` and append the port as shown above.

## Database bootstrap
1) Create schema:  
`sqlcmd -S localhost,56539 -U <user> -P <pass> -i scripts/create_tables.sql`

2) Seed demo data:  
`sqlcmd -S localhost,56539 -U <user> -P <pass> -i scripts/seed_data.sql`

- Demo customers: `cust1/0001`, `cust2/0002`, ... up to `cust100/0100`  
- Demo employees: `teller1/3333`, `teller2/3334`, `officer1/4444`, `ops1/5555`  
- Seed script loads 100 customers, 300 accounts, 30 loans, transactions, transfers, and overdraft events for testing.

## Run the app
```
streamlit run app.py
```

## Repository map
- `app.py`: Streamlit UI entry point and navigation.
- `controllers/`: Use-case orchestration; validation and presentation shaping.
- `daos/`: Parameterized SQL for accounts, transactions, transfers, loans, overdrafts, reporting, and auth.
- `entities/`: Dataclass models aligned to table schemas.
- `infra/`: Shared infrastructure (DB engine/pool factory).
- `scripts/`: SQL for schema creation, seeding, and reporting samples.
- `docs/`: SQL references and explanations (`docs/all_queries.md`, `docs/queries.md`).
- `assets/`: UI assets (logo).

## Handy references
- SQL walkthroughs plus business framing for each query: `docs/all_queries.md` (runnable samples in `scripts/report_queries.sql`).  
- Architecture/walking-skeleton blueprint: `WALKING_SKELETON.md`.

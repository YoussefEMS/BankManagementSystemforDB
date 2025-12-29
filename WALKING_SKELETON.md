# Walking Skeleton - Portsaid International Bank (Python + Streamlit Blueprint)

## Architecture
- 3-layer, BCE-inspired: Boundary/UI  Controllers  Entities  Persistence; Infrastructure underpins persistence; Auth/Context is a small support slice.
- Flow: UI calls controllers; controllers orchestrate DAOs and format results; DAOs map SQL rows to entities using a pooled data source; entities stay passive/data-only.
- Goal: replicate this shape and implement all 12 use cases in Python/Streamlit.

## Layers and Roles
- UI (boundary): Streamlit pages for login, account selection, balances, transaction history, transfers, deposits, withdrawals, loans, statuses, alerts, admin/ops views. Input capture + rendering only.
- Controllers: One per use case/cluster. Validate/normalize input, call DAOs, shape results for UI (formatting, table rows). No SQL.
- Entities: Plain data holders (e.g., Account, Customer, Transaction, Loan, Transfer, OverdraftEvent, InterestPosting). Use Python dataclasses; no outward deps.
- Persistence (DAOs): Parameterized SQL with optional filters; map rows  entities; hidden behind controllers; use a pooled engine.
- Infrastructure: Engine/pool factory reading config; shared by DAOs.
- Auth/Context: Session holder for logged-in customer plus auth service/controller exposing account lists, name, id.

## Data Access Pattern
- Prepared/parameterized queries; add optional filters conditionally (date range, type, status).
- Map SQL types to domain types (timestamps  datetime, numerics  Decimal).
- Predictable ordering (e.g., transactions by timestamp DESC).
- Return empty collections for "not found" rather than raising in controllers.
- Central pool/engine configured from a properties/.env file.

## Configuration (Python/Streamlit)
- Config/.env keys: DB_URL, DB_USER, DB_PASSWORD, DB_DRIVER, POOL_MAX_SIZE, POOL_MIN_IDLE, POOL_IDLE_TIMEOUT_MS, POOL_MAX_LIFETIME_MS, POOL_CONNECTION_TIMEOUT_MS.
- Mirror pool knobs from the Java setup (max size, min idle, timeouts, lifetimes).

## Use-Case Coverage (12 UCs)
- Apply the same layering for all 12: UI  Controller  DAO  DB.
- Listing/filtering UCs (e.g., transaction history): optional filters with "All" sentinels.
- State-changing UCs (e.g., transfers, deposits, withdrawals, status updates): business logic in controllers, SQL in DAOs, consistent DB transactions.

## UI Guidelines (Streamlit)
- Dropdowns for account selection from logged-in user.
- Date pickers for ranges; selects with "All" for type/status.
- Tables with formatted fields (amounts to 2 decimals; formatted timestamps).
- Prefer empty results + gentle messages over exceptions for "not found".

## Layering Rules
- UI  Controllers  DAOs/Entities; DAOs  Infrastructure/Entities; Entities depend on nothing outward.
- Auth/context accessed via an auth controller/service; UI may call it for session/account info.
- Avoid controller-to-controller reach-through unless explicitly coordinated; entities never know about DAOs.

## Database Sketch (to port)
- Core tables: Accounts (account_number PK, customer_id FK, type, balance, currency, status, date_opened); Customers; Transactions (transaction_id PK, account_number FK, type, amount, timestamp, performed_by, note, balance_after, reference_code); plus loan/overdraft/transfer tables for related UCs.
- Parameterized queries with optional filters; defined ordering (e.g., timestamp DESC).

## Implementation Checklist
- [ ] Define modules/packages: ui/, controllers/, entities/, daos/, infra/ (engine), auth/.
- [ ] Add config loader (.env) and engine/pool factory.
- [ ] Create dataclasses for entities matching DB schema.
- [ ] Implement DAOs with parameterized SQL + optional filters; return entities/lists; no UI formatting.
- [ ] Implement controllers per UC; handle validation/normalization and UI-ready formatting.
- [ ] Build Streamlit pages per UC; reuse table/form components; keep logic out of UI.
- [ ] Enforce non-error UX: empty results for "not found"; concise user messages.

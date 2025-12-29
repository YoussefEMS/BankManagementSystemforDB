from decimal import Decimal
from infra.db import get_engine
from daos import AccountDAO, TransactionDAO, TransferDAO, OverDraftEventDAO
from entities import Transfer


class TransferController:
    def __init__(self):
        self.account_dao = AccountDAO()
        self.transaction_dao = TransactionDAO()
        self.transfer_dao = TransferDAO()
        self.overdraft_dao = OverDraftEventDAO()
        self.engine = get_engine()

    def transfer(self, from_account: str, to_account: str, amount: Decimal, performed_by: str, note: str | None = None) -> Transfer:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        source = self.account_dao.get_one(from_account)
        dest = self.account_dao.get_one(to_account)
        if not source or not dest:
            raise ValueError("Source or destination account not found")
        if source.status.upper() != "ACTIVE":
            raise ValueError("Source account not active")
        if dest.status.upper() != "ACTIVE":
            raise ValueError("Destination account not active")
        if source.balance < amount:
            self.overdraft_dao.add_event(
                account_number=from_account,
                amount=amount,
                balance_after=source.balance,
                note="Overdraft transfer attempt",
            )
            raise ValueError("Insufficient funds (overdraft recorded)")

        new_source_balance = source.balance - amount
        new_dest_balance = dest.balance + amount

        with self.engine.begin() as conn:
            self.account_dao.update_balance(from_account, new_source_balance, conn=conn)
            self.account_dao.update_balance(to_account, new_dest_balance, conn=conn)
            transfer_id = self.transfer_dao.add(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                status="COMPLETED",
                note=note,
                conn=conn,
            )
            # Mirror into transaction log for both accounts
            self.transaction_dao.add(
                account_number=from_account,
                transaction_type="TRANSFER_OUT",
                amount=amount,
                performed_by=performed_by,
                note=note,
                balance_after=new_source_balance,
                reference_code=str(transfer_id),
                conn=conn,
            )
            self.transaction_dao.add(
                account_number=to_account,
                transaction_type="TRANSFER_IN",
                amount=amount,
                performed_by=performed_by,
                note=note,
                balance_after=new_dest_balance,
                reference_code=str(transfer_id),
                conn=conn,
            )

        transfer = self.transfer_dao.list_for_account(from_account)
        # Return the first matching transfer_id (freshest)
        for t in transfer:
            if t.transfer_id == transfer_id:
                return t
        raise RuntimeError("Transfer not found after creation")

    def list_history(self, account_number: str) -> list[Transfer]:
        return self.transfer_dao.list_for_account(account_number)

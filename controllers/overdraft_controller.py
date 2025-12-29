from daos import OverDraftEventDAO
from entities import OverDraftEvent


class OverDraftController:
    def __init__(self):
        self.dao = OverDraftEventDAO()

    def list_events(self, account_number: str) -> list[OverDraftEvent]:
        return self.dao.list_for_account(account_number)

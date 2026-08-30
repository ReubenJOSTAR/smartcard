"""Shopping session business logic — placeholder. See progress.md → Backend — Sessions."""


class SessionService:
    async def create_session(self, user_id: str, store_name_text: str, budget_paise: int) -> dict:
        ...

    async def add_item(self, session_id: str, barcode: str, quantity: int) -> dict:
        ...

    async def finish_session(self, session_id: str) -> dict:
        ...

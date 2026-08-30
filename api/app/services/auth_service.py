"""Auth business logic — placeholder. See progress.md → Backend — Auth."""


class AuthService:
    async def send_otp(self, phone: str) -> None:
        ...

    async def verify_otp(self, phone: str, otp: str) -> dict:
        ...

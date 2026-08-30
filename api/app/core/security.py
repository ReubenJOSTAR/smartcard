"""JWT creation/verification, OTP hashing, lockout logic — placeholder.
See progress.md → Backend — Auth.
"""


def create_access_token(user_id: str, phone: str) -> str:
    ...


def create_refresh_token(user_id: str) -> str:
    ...


def decode_token(token: str) -> dict:
    ...


def hash_otp(otp: str) -> str:
    ...


def verify_otp(otp: str, hashed: str) -> bool:
    ...

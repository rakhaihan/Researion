import re

PASSWORD_MIN_LENGTH = 8
_LETTER_RE = re.compile(r"[A-Za-z]")
_DIGIT_RE = re.compile(r"\d")


def validate_password_strength(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    if not _LETTER_RE.search(password):
        raise ValueError("Password must contain at least one letter.")
    if not _DIGIT_RE.search(password):
        raise ValueError("Password must contain at least one number.")

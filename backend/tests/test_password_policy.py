import pytest
from pydantic import ValidationError

from app.core.password_policy import validate_password_strength
from app.schemas.auth import RegisterRequest


def test_password_requires_letter_and_number():
    with pytest.raises(ValueError, match="letter"):
        validate_password_strength("12345678")
    with pytest.raises(ValueError, match="number"):
        validate_password_strength("abcdefgh")


def test_register_schema_enforces_policy():
    with pytest.raises(ValidationError):
        RegisterRequest(full_name="Test User", email="t@example.com", password="allletters")
    req = RegisterRequest(full_name="Test User", email="t@example.com", password="secure123")
    assert req.password == "secure123"

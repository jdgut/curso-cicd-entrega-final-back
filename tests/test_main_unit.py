from app.core.database import SessionLocal
from app.main import _hash_password, _parse_allowed_origins, seed_demo_users
from app.models.domain import User


def test_parse_allowed_origins_wildcard() -> None:
    assert _parse_allowed_origins("*") == ["*"]


def test_parse_allowed_origins_normalizes_and_deduplicates() -> None:
    parsed = _parse_allowed_origins(
        " https://example.com/ , https://example.com, http://localhost:5173 ,, http://localhost:5173/ "
    )
    assert parsed == ["https://example.com", "http://localhost:5173"]


def test_hash_password_returns_salt_and_digest() -> None:
    encoded = _hash_password("testtest")
    salt, digest = encoded.split("$", maxsplit=1)

    assert len(salt) == 32
    assert len(digest) == 64
    assert encoded != _hash_password("testtest")


def test_seed_demo_users_is_idempotent() -> None:
    seed_demo_users()
    seed_demo_users()

    with SessionLocal() as db:
        emails = [row[0] for row in db.query(User.email).all()]

    assert len(emails) == 15
    assert len(set(emails)) == 15
    assert "test1@eafit.edu.co" in emails
    assert "test15@eafit.edu.co" in emails

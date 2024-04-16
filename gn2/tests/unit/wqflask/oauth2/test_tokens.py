"""Test oauth2 jwt tokens"""
from gn2.wqflask.oauth2.tokens import JWTToken


JWT_BEARER_TOKEN = b"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIs\
ImN0eSI6Impzb24ifQ.eyJpc3MiOiJHTjIiLCJ\
zdWIiOiIxMjM0IiwiYXVkIjoiR04yIiwiZXhwI\
joiMTIzNDUifQ.ETSr_7O4ZWLac5l4pinO9Xeb\
mzTO7xp_LvbgxjnskDc"


def test_encode_token():
    """Test encoding a jwt token."""
    token = JWTToken(
        key="secret",
        registered_claims={
            "iss": "GN2",
            "sub": "1234",
            "aud": "GN2",
            "exp": "12345",
        }
    )
    assert token.encode() == JWT_BEARER_TOKEN
    assert token.bearer_token == {
        "Authorization": f"Bearer {JWT_BEARER_TOKEN}"
    }


def test_decode_token():
    """Test decoding a jwt token."""
    claims = JWTToken.decode(JWT_BEARER_TOKEN, "secret")
    assert claims == {
        'iss': 'GN2',
        'sub': '1234',
        'aud': 'GN2',
        'exp': '12345'
    }

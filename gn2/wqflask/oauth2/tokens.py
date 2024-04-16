"""This file contains functions/classes related to dealing with JWTs"""
from dataclasses import dataclass
from dataclasses import field
from authlib.jose import jwt


@dataclass
class JWTToken:
    """Class for constructing a JWT according to RFC7519

https://datatracker.ietf.org/doc/html/rfc7519

    """
    key: str
    private_claims: dict = field(default_factory=lambda: {})
    public_claims: dict = field(default_factory=lambda: {})
    jose_header: dict = field(
        default_factory=lambda: {
            "alg": "HS256",
            "typ": "jwt",
            "cty": "json",
        })
    registered_claims: dict = field(
        default_factory={
            "iss": "",  # Issuer Claim
            "iat": "",  # Issued At
            "sub": "",  # Subject Claim
            "aud": "",  # Audience Claim
            "exp": "",  # Expiration Time Claim
            "jti": "",  # Unique Identifier for this token
        })

    def __post__init__(self):
        match self.jose_header.get("alg"):
            case "HS256":
                self.key = self.key
            case _:
                with open(self.key, "rb")as f_:
                    self.key = f_.read()

    def encode(self):
        """Encode the JWT"""
        payload = self.registered_claims \
            | self.private_claims \
            | self.public_claims \
            | self.registered_claims
        return jwt.encode(self.jose_header, payload, self.key)

    @property
    def bearer_token(self) -> dict:
        """Return a header that contains this tokens Bearer Token"""
        return {
            "Authorization": f"Bearer {self.encode()}"
        }

    @staticmethod
    def decode(token, key) -> str:
        """Decode the JWT"""
        return jwt.decode(token, key)

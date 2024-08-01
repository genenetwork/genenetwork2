"""Utilities dealing with JSON Web Keys (JWK)"""
import os
from pathlib import Path
from typing import Any, Union
from datetime import datetime, timedelta

from flask import Flask
from authlib.jose import JsonWebKey
from pymonad.either import Left, Right, Either

def jwks_directory(app: Flask, configname: str) -> Path:
    """Compute the directory where the JWKs are stored."""
    appsecretsdir = Path(app.config[configname]).parent
    if appsecretsdir.exists() and appsecretsdir.is_dir():
        jwksdir = Path(appsecretsdir, "jwks/")
        if not jwksdir.exists():
            jwksdir.mkdir()
        return jwksdir
    raise ValueError(
        "The `appsecretsdir` value should be a directory that actually exists.")


def generate_and_save_private_key(
        storagedir: Path,
        kty: str = "RSA",
        crv_or_size: Union[str, int] = 2048,
        options: tuple[tuple[str, Any]] = (("iat", datetime.now().timestamp()),)
) -> JsonWebKey:
    """Generate a private key and save to `storagedir`."""
    privatejwk = JsonWebKey.generate_key(
        kty, crv_or_size, dict(options), is_private=True)
    keyname = f"{privatejwk.thumbprint()}.private.pem"
    with open(Path(storagedir, keyname), "wb") as pemfile:
        pemfile.write(privatejwk.as_pem(is_private=True))

    return privatejwk


def pem_to_jwk(filepath: Path) -> JsonWebKey:
    """Parse a PEM file into a JWK object."""
    with open(filepath, "rb") as pemfile:
        return JsonWebKey.import_key(pemfile.read())


def __sorted_jwks_paths__(storagedir: Path) -> tuple[tuple[float, Path], ...]:
    """A sorted list of the JWK file paths with their creation timestamps."""
    return tuple(sorted(((os.stat(keypath).st_ctime, keypath)
                         for keypath in (Path(storagedir, keyfile)
                                         for keyfile in os.listdir(storagedir)
                                         if keyfile.endswith(".pem"))),
                        key=lambda tpl: tpl[0]))


def list_jwks(storagedir: Path) -> tuple[JsonWebKey, ...]:
    """
    List all the JWKs in a particular directory in the order they were created.
    """
    return tuple(pem_to_jwk(keypath) for ctime,keypath in
                 __sorted_jwks_paths__(storagedir))


def newest_jwk(storagedir: Path) -> Either:
    """
    Return an Either monad with the newest JWK or a message if none exists.
    """
    existingkeys = __sorted_jwks_paths__(storagedir)
    if len(existingkeys) > 0:
        return Right(pem_to_jwk(existingkeys[-1][1]))
    return Left("No JWKs exist")


def newest_jwk_with_rotation(jwksdir: Path, keyage: int) -> JsonWebKey:
    """
    Retrieve the latests JWK, creating a new one if older than `keyage` days.
    """
    def newer_than_days(jwkey):
        filestat = os.stat(Path(
            jwksdir, f"{jwkey.as_dict()['kid']}.private.pem"))
        oldesttimeallowed = (datetime.now() - timedelta(days=keyage))
        if filestat.st_ctime < (oldesttimeallowed.timestamp()):
            return Left("JWK is too old!")
        return jwkey

    return newest_jwk(jwksdir).then(newer_than_days).either(
        lambda _errmsg: generate_and_save_private_key(jwksdir),
        lambda key: key)

import hmac
import hashlib

# Replace this because it just wraps around Python3's internal
# functions. Added this during migration.


def pbkdf2_hex(data, salt, iterations=1000, keylen=24, hashfunc="sha1"):
    """Wrapper function of python's hashlib.pbkdf2_hmac.
    """

    dk = hashlib.pbkdf2_hmac(hashfunc,
                             bytes(data, "utf-8"),  # password
                             salt,
                             iterations,
                             keylen)
    return dk.hex()


def safe_str_cmp(a, b):
    def __str_to_bytes__(value):
        if isinstance(value, str):
            return value.encode("utf8")
        return value

    return hmac.compare_digest(__str_to_bytes__(a), __str_to_bytes(b))

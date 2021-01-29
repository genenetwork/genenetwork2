import hashlib

from werkzeug.security import safe_str_cmp as ssc

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
    return ssc(a, b)

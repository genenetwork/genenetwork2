"""requests but with monads"""
import requests
from pymonad.either import Left, Right, Either

def __wrap_response__(resp) -> Either:
    if resp.status_code == 200:
        return Right(resp)
    return Left(resp)

def get(url, params=None, **kwargs) -> Either:
    """Wrap requests get method with Either monad"""
    return __wrap_response__(requests.get(url, params=params, **kwargs))

def post(url, data=None, json=None, **kwargs) -> Either:
    """Wrap requests post method with Either monad"""
    return __wrap_response__(requests.post(url, data=data, json=json, **kwargs))


def put(url, data=None, json=None, **kwargs) -> Either:
    """Wrap requests put  method with Either monad"""
    return __wrap_response__(requests.put(url, data=data, json=json, **kwargs))


def delete(url,  **kwargs) -> Either:
    """Wrap requests delete  method with Either monad"""
    return __wrap_response__(requests.delete(url,  **kwargs))

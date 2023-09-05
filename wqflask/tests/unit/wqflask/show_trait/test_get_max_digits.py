import pytest
import unittest

from wqflask.show_trait.show_trait import get_max_digits

@unittest.skip("Too complicated")
@pytest.mark.parametrize(
    "trait_vals,expected",
    (((
        (0, 1345, 92, 734),
        (234253, 33, 153, 5352),
        (3542, 24, 135)),
      [3, 5, 3]),))
def test_get_max_digits(trait_vals, expected):
    assert get_max_digits(trait_vals) == expected

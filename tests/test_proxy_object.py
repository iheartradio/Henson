"""Test the utils module."""

import pytest

from henson.utils import ProxyObject


def test_callable():
    """Test that the proxied object can be a callable."""
    f = lambda: 42
    expected = 42
    actual = ProxyObject(f)
    assert actual == expected


@pytest.mark.parametrize('f', (str, repr, hash, bool))
def test_data_model_basic(f):
    """Test the basic methods of the data model."""
    expected = f(42)
    actual = f(ProxyObject(42))
    assert actual == expected


def test_data_model_compare_equal_to():
    """Test equal to comparisons."""
    assert ProxyObject(41) == 41
    assert ProxyObject(42) == 42
    assert ProxyObject(43) == 43


def test_data_model_compare_greater_than():
    """Test greater than comparisons."""
    proxied = ProxyObject(42)
    assert proxied > 41
    assert not (proxied > 42)
    assert not (proxied > 43)


def test_data_model_compare_greater_than_equal_to():
    """Test greater than or equal to comparisons."""
    proxied = ProxyObject(42)
    assert proxied >= 41
    assert proxied >= 42
    assert not (proxied >= 43)


def test_data_model_compare_less_than():
    """Test less than comparisons."""
    proxied = ProxyObject(42)
    assert not (proxied < 41)
    assert not (proxied < 42)
    assert proxied < 43


def test_data_model_compare_less_than_equal_to():
    """Test less than or equal to comparisons."""
    proxied = ProxyObject(42)
    assert not (proxied <= 41)
    assert proxied <= 42
    assert proxied <= 43


def test_data_model_compare_not_equal():
    """Test not equal comparisons."""
    assert ProxyObject(42) != 41
    assert ProxyObject(42) != 43


def test_data_model_container_contains():
    """Test containment."""
    proxied = ProxyObject([42, 43])
    assert 42 in proxied
    assert 43 in proxied
    assert 44 not in proxied


def test_data_model_container_len():
    """Test length."""
    expected = 2
    actual = len(ProxyObject([42, 43]))
    assert actual == expected


def test_data_model_numeric_abs():
    """Test absolute value."""
    expected = 42
    actual = abs(ProxyObject(-42))
    assert actual == expected


@pytest.mark.parametrize('proxy_value, value, expected', (
    (42, 1, 43),
    ('spam', 'eggs', 'spameggs'),
    ([1], [2], [1, 2]),
))
def test_data_model_numeric_add(proxy_value, value, expected):
    """Test addition."""
    assert ProxyObject(proxy_value) + value == expected
    # While adding integers is commutative, adding other types isn't.
    assert proxy_value + ProxyObject(value) == expected


def test_data_model_numeric_and():
    """Test bitwise and."""
    proxied = ProxyObject(42)
    assert proxied & 2 == 2
    assert 2 & proxied == 2


def test_data_model_numeric_division():
    """Test division."""
    proxied = ProxyObject(42)
    assert proxied / 1 == 42
    assert 21 / proxied == 0.5


def test_data_model_numeric_divmod():
    """Test divmod."""
    proxied = ProxyObject(42)
    assert divmod(proxied, 4) == (10, 2)
    assert divmod(43, proxied) == (1, 1)


def test_data_model_numeric_float():
    """Test the float constructor."""
    assert float(ProxyObject('42.1')) == 42.1


def test_data_model_numeric_floor():
    """Test floor division."""
    proxied = ProxyObject(42)
    assert proxied // 3 == 14
    assert 85 // proxied == 2


def test_data_model_numeric_int():
    """Test the int constructor."""
    expected = 42
    actual = int(ProxyObject('42'))
    assert actual == expected


def test_data_model_numeric_invert():
    """Test the inversion operator."""
    expected = -43
    actual = ~ProxyObject(42)
    assert actual == expected


def test_data_model_numeric_mod():
    """Test modulo operation."""
    proxied = ProxyObject(42)
    assert proxied % 4 == 2
    assert 43 % proxied == 1


@pytest.mark.parametrize('proxy_value, value, expected', (
    (42, 2, 84),
    ('spam', 2, 'spamspam'),
    ([1], 2, [1, 1]),
))
def test_data_model_numeric_mul(proxy_value, value, expected):
    """Test multiplication."""
    assert ProxyObject(proxy_value) * value == expected
    assert value * ProxyObject(proxy_value) == expected


def test_data_model_numeric_or():
    """Test bitwise or."""
    proxied = ProxyObject(42)
    assert proxied | 2 == 42
    assert 2 | proxied == 42


def test_data_model_numeric_neg():
    """Test the negation operator."""
    expected = -42
    actual = -ProxyObject(42)
    assert actual == expected


def test_data_model_numeric_pos():
    """Test the positive unary operator."""
    expected = -42
    actual = +ProxyObject(-42)
    assert actual == expected


def test_data_model_numeric_pow():
    """Test power."""
    proxied = ProxyObject(42)
    assert proxied ** 2 == 1764
    assert 2 ** proxied == 4398046511104


def test_data_model_numeric_round():
    """Test rounding."""
    expected = 43.0
    actual = round(ProxyObject(42.6))
    assert actual == expected


def test_data_model_numeric_sub():
    """Test subtraction."""
    proxied = ProxyObject(42)
    assert proxied - 1 == 41
    assert 43 - proxied == 1


def test_data_model_numeric_xor():
    """Test bitwise xor."""
    proxied = ProxyObject(42)
    assert proxied ^ 2 == 40
    assert 2 ^ proxied == 40


def test_is_original():
    """Test that the proxied object is the original."""
    expected = {'a': 1}
    actual = ProxyObject(expected)
    actual['b'] = 2
    assert actual == expected


def test_is_original_type():
    """Test that the proxied object is the original type."""
    assert isinstance(ProxyObject(42), int)


def test_is_proxy_type():
    """Test that the proxied object is a ProxyObject."""
    assert isinstance(ProxyObject(42), ProxyObject)

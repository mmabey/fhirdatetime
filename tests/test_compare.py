# -*- coding: utf-8 -*-
"""Test for comparisons of DateTime and other objects."""

from datetime import date, datetime, timedelta, timezone

import pytest

from fhirdatetime import DateTime


def idfn(val):
    """Create a string ID for the test values."""
    return f" {val} "


# Handy timezones
utc = timezone.utc
ten_behind = timezone(timedelta(hours=-10))

eq = [
    (
        DateTime(year=2020),
        DateTime(year=2020),
    ),
    (
        DateTime(year=2020, month=1),
        DateTime(year=2020, month=1),
    ),
    (
        DateTime(year=2020, month=1, day=6),
        DateTime(year=2020, month=1, day=6),
    ),
    (
        DateTime(year=2020, month=1, day=6, hour=12, minute=30),
        DateTime(year=2020, month=1, day=6, hour=12, minute=30),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, 8, 209495),
        DateTime(2020, 1, 6, 12, 30, 8, 209495),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, 8, 209495),
        datetime(2020, 1, 6, 12, 30, 8, 209495),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, tzinfo=utc),
        DateTime(2020, 1, 6, 2, 30, tzinfo=ten_behind),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, tzinfo=utc),
        datetime(2020, 1, 6, 2, 30, tzinfo=ten_behind),
    ),
    (  # Switches order of previous case
        datetime(2020, 1, 6, 2, 30, tzinfo=ten_behind),
        DateTime(2020, 1, 6, 12, 30, tzinfo=utc),
    ),
    (
        DateTime(2020, 1, 6),
        date(2020, 1, 6),
    ),
    (  # Switches order of previous case
        date(2020, 1, 6),
        DateTime(2020, 1, 6),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, 8, 209495),
        date(2020, 1, 6),
    ),
    (
        DateTime(2020, 1, 6, 12, 30, 8, tzinfo=ten_behind),
        date(2020, 1, 6),
    ),
    (
        DateTime(2021),
        DateTime(2021, 12),
    ),
    (  # Switches order of previous case
        DateTime(2021, 12),
        DateTime(2021),
    ),
    (
        DateTime(2021, 4, 21, 1, 32, 44, tzinfo=utc),
        DateTime(2021),
    ),
    (  # Switches order of previous case
        DateTime(2021),
        DateTime(2021, 4, 21, 1, 32, 44, tzinfo=utc),
    ),
    (
        datetime(2021, 4, 21, 1, 32, 44, tzinfo=utc),
        DateTime(2021),
    ),
    (
        DateTime(2021),
        datetime(2021, 4, 21, 1, 32, 44, tzinfo=utc),
    ),
    (  # Tests leap year math
        DateTime(2020, 2, 29, 19, 0, 2, tzinfo=ten_behind),
        DateTime(2020, 3, 1, 5, 0, 2, tzinfo=utc),
    ),
]

eq_xf = [
    (
        DateTime(2021, 4, 21, 1, 32, 44, tzinfo=utc),
        DateTime(2021).isoformat(),
    ),
    (DateTime(2021), {2021}),
    (DateTime(2021), [2021]),
    (DateTime(2021), (2021,)),
]

gt = [
    (
        DateTime(year=2021),
        DateTime(year=2020),
    ),
    (
        DateTime(2021, 4, 21, 8, 7, 6, tzinfo=ten_behind),
        DateTime(2021, 4, 21, 8, 7, 6, tzinfo=utc),
    ),
    (
        date(2021, 4, 21),
        DateTime(2020),
    ),
    (
        DateTime(2022),
        date(2021, 4, 21),
    ),
    (
        datetime(2021, 4, 21, 12, 12, 12, tzinfo=utc),
        DateTime(2020),
    ),
    (  # Tests leap year math
        DateTime(2020, 2, 29, 19, 0, 3, tzinfo=ten_behind),
        DateTime(2020, 3, 1, 5, 0, 2, tzinfo=utc),
    ),
]

lt = [(b, a) for a, b in gt]


@pytest.mark.parametrize("obj_a, obj_b", eq, ids=idfn)
def test_eq(obj_a, obj_b):
    """Tests for equality."""
    assert obj_a == obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq_xf + gt + lt, ids=idfn)
@pytest.mark.xfail(raises=(AssertionError, TypeError), strict=True)
def test_eq_fail(obj_a, obj_b):
    """Tests for equality that should fail."""
    assert obj_a == obj_b


@pytest.mark.parametrize("obj_a, obj_b", gt + lt, ids=idfn)
def test_ne(obj_a, obj_b):
    """Tests for inequality."""
    assert obj_a != obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq, ids=idfn)
@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_ne_fail(obj_a, obj_b):
    """Tests for inequality that should fail."""
    assert obj_a != obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq + gt, ids=idfn)
def test_ge(obj_a, obj_b):
    """Tests for greater than or equal to."""
    assert obj_a >= obj_b


@pytest.mark.parametrize("obj_a, obj_b", lt, ids=idfn)
@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_ge_fail(obj_a, obj_b):
    """Tests for greater than or equal to that should fail."""
    assert obj_a >= obj_b


@pytest.mark.parametrize("obj_a, obj_b", gt, ids=idfn)
def test_gt(obj_a, obj_b):
    """Tests for greater than."""
    assert obj_a > obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq + lt, ids=idfn)
@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_gt_fail(obj_a, obj_b):
    """Tests for greater than that should fail."""
    assert obj_a > obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq + lt, ids=idfn)
def test_le(obj_a, obj_b):
    """Tests for less than or equal."""
    assert obj_a <= obj_b


@pytest.mark.parametrize("obj_a, obj_b", gt, ids=idfn)
@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_le_fail(obj_a, obj_b):
    """Tests for less than or equal that should fail."""
    assert obj_a <= obj_b


@pytest.mark.parametrize("obj_a, obj_b", lt, ids=idfn)
def test_lt(obj_a, obj_b):
    """Tests for less than."""
    assert obj_a < obj_b


@pytest.mark.parametrize("obj_a, obj_b", eq + gt, ids=idfn)
@pytest.mark.xfail(raises=AssertionError, strict=True)
def test_lt_fail(obj_a, obj_b):
    """Tests for less than that should fail."""
    assert obj_a < obj_b

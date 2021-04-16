# -*- coding: utf-8 -*-
"""Test parameters of creating DateTime objects."""

from datetime import date, datetime, time
from typing import Union

import pytest

from fhirdatetime import DateTime, __version__


def test_version():
    """Check library version is what it should be."""
    assert __version__ == "0.1.0"


def compare_native(dt: DateTime, other: Union[date, datetime]):
    """Check values when obj is created from a native type."""
    assert dt.year == other.year
    assert dt.month == other.month
    assert dt.day == other.day

    if isinstance(other, datetime):
        assert dt.hour == other.hour
        assert dt.minute == other.minute
        assert dt.second == other.second
        assert dt.microsecond == other.microsecond
        assert dt.tzinfo == other.tzinfo
        assert dt.fold == other.fold


def make_and_assert(params: dict):
    """Create and run tests on a DateTime object."""
    dt = DateTime(**params)
    if isinstance(params["year"], (date, datetime)):
        return compare_native(dt, params["year"])

    if isinstance(params["year"], str):
        # There's not really a good way to test string parsing without writing a second
        # string parser, in which case you have two things to make sure are correct...
        return

    params_set = set(params.keys())
    none_params = {"year", "month", "day", "hour", "minute"} - params_set
    for p in none_params:
        assert getattr(dt, p) is None

    zero_params = {"second", "microsecond"} - params_set
    for p in zero_params:
        assert getattr(dt, p) == 0

    for p in params_set - none_params - zero_params:
        assert getattr(dt, p) == params.get(p)


cases = {
    "success": [
        {"year": 2011},
        {"year": 1909, "month": 9},
        {"year": 30, "month": 2, "day": 28},
        {"year": 2030, "month": 2, "day": 28, "hour": 14, "minute": 54},
        {
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 23,
            "minute": 53,
            "second": 6,
            "microsecond": 999_999,  # Max value for microsecond
        },
        {"year": datetime(2011, 9, 12, 14, 53)},
        {"year": date(2011, 9, 12)},
        {"year": "2011"},
        {"year": "2011-09"},
        {"year": "2011-09-12"},
        {"year": "2011-09-12T12:14"},
        {"year": "2011-09-12T12:14:31-06:00"},
    ],
    "fail_type": [
        {"year": None},
        {"year": time(12, 15)},
    ],
    "fail_value": [
        {"year": 19999},
        {"year": 2030, "month": 2, "day": 28, "hour": 14},
        {"year": 2030, "month": 20, "day": 28},
        {"year": 2030, "month": 2, "day": 30},
        {"year": 2030, "month": 2, "day": 28, "hour": 24, "minute": 0},
        {"year": 2030, "month": 2, "day": 28, "hour": 23, "minute": 60},
        {"year": 2030, "month": 2, "day": 28, "hour": 23, "minute": 0, "second": 60},
        {
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 23,
            "minute": 0,
            "second": 6,
            "microsecond": 1_999_999,
        },
        {"year": "2011-09-1212:14"},
    ],
}


@pytest.mark.parametrize("params", cases["success"])
def test_creation(params: dict):
    """Test creation of a DateTime object with given params."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_type"])
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_bad_creation_type(params: dict):
    """Test creation of a DateTime object that should fail with TypeError."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_value"])
@pytest.mark.xfail(raises=ValueError, strict=True)
def test_bad_creation_value(params: dict):
    """Test creation of a DateTime object that should fail with ValueError."""
    make_and_assert(params)

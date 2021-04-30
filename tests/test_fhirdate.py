# -*- coding: utf-8 -*-
"""Test parameters of creating FhirDate objects."""

import random
import time as _time
from datetime import date, datetime, time, timezone

import pytest

from fhirdatetime import FhirDate

random.seed()


def compare_native(d: FhirDate, other: date):
    """Check values when obj is created from a native type."""
    assert d.year == other.year
    assert d.month == other.month
    assert d.day == other.day


def make_and_assert(params: dict):
    """Create and run tests on a FhirDate object."""
    d = FhirDate(**params)
    if isinstance(params["year"], date):
        return compare_native(d, params["year"])

    if isinstance(params["year"], str):
        # There's not really a good way to test string parsing without writing a second
        # string parser, in which case you have two things to make sure are correct...
        return

    params_set = set(params.keys())
    none_params = {"year", "month", "day"} - params_set
    for p in none_params:
        assert getattr(d, p) is None

    for p in params_set - none_params:
        assert getattr(d, p) == params.get(p)


cases = {
    "success": [
        {"year": 2011},
        {"year": 1909, "month": 9},
        {"year": 30, "month": 2, "day": 28},
        {"year": date(2011, 9, 12)},
        {"year": "2011"},
        {"year": "2011-09"},
        {"year": "2011-09-12"},
    ],
    "fail_type": [
        {"year": None},
        {"year": time(12, 15)},
        {"year": 2021, "month": 2, "day": 28, "tzinfo": timezone.utc},  # No time
    ],
    "fail_value": [
        {"year": 19999},  # Year out of range
        {"year": 2030, "month": 20, "day": 28},  # month out of range
        {"year": 2030, "month": 2, "day": 30},  # day out of range
        {"year": 2021, "day": 13},  # No month
    ],
}


@pytest.mark.parametrize(
    "param",
    (
        date.today().isoformat(),
        datetime.utcnow().isoformat(),
        {"year": 2030, "month": 2, "day": 28, "hour": 14, "minute": 54},
        "2011-09-12T12:14:31-06:00",
    ),
)
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_from_native_xfail(param):
    """Test creation of a FhirDate from a native object, should fail."""
    FhirDate.from_native(param)


@pytest.mark.parametrize("params", cases["success"])
def test_creation(params: dict):
    """Test creation of a FhirDate object with given params."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_type"])
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_bad_creation_type(params: dict):
    """Test creation of a FhirDate object that should fail with TypeError."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_value"])
@pytest.mark.xfail(raises=ValueError, strict=True)
def test_bad_creation_value(params: dict):
    """Test creation of a FhirDate object that should fail with ValueError."""
    make_and_assert(params)


def test_getitem():
    """Test accessing an invalid index raises an error."""
    d = FhirDate(**random.choice(cases["success"]))
    min_ = 0
    max_ = 2
    for _ in range(100):
        with pytest.raises(IndexError):
            _ = d[random.randrange(min_ - 1, -2000, -1)]
        with pytest.raises(IndexError):
            _ = d[random.randrange(max_ + 1, 2000)]


def test_other_methods():
    """Test other methods, mostly for coverage."""
    d = FhirDate(2020, 5, 4)

    assert d.timetuple() == _time.struct_time((2020, 5, 4, 0, 0, 0, 0, 125, -1))

    assert d.isoformat() == "2020-05-04"
    with pytest.raises(ValueError):
        FhirDate.fromisoformat("2020*02*13")

    assert d.weekday() == 0
    assert d.isoweekday() == 1
    assert d.isocalendar() == (2020, 19, 1)

    assert str(FhirDate("2020")) == "2020"
    assert str(FhirDate("2020-05")) == "2020-05"
    assert str(FhirDate("2020-05-04")) == "2020-05-04"

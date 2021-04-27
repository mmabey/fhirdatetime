# -*- coding: utf-8 -*-
"""Test parameters of creating FhirDateTime objects."""

import random
import sys
import time as _time
from datetime import date, datetime, time, timedelta, timezone
from typing import Union

import pytest

from fhirdatetime import FhirDateTime, __version__

random.seed()


def test_version():
    """Check library version is what it should be."""
    ver = "0.1.0b8"
    assert __version__ == ver
    with open("pyproject.toml") as proj:
        for line in proj:
            if line.startswith("version = "):
                assert line == f'version = "{ver}"\n'
                return
    raise ValueError("Unable to find version string in pyproject.toml")


def compare_native(dt: FhirDateTime, other: Union[date, datetime]):
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
    """Create and run tests on a FhirDateTime object."""
    dt = FhirDateTime(**params)
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
        {
            "year": datetime(
                2020, 11, 1, 23, 53, tzinfo=timezone(timedelta(hours=-6)), fold=1
            )
        },
        {"year": date(2011, 9, 12)},
        {"year": "2011"},
        {"year": "2011-09"},
        {"year": "2011-09-12"},
        {"year": "2011-09-12T12:14"},
        {"year": "2011-09-12T12:14:31-06:00"},
        {"year": "2016-01-26T21:58:41.000Z"},
    ],
    "fail_type": [
        {"year": None},
        {"year": time(12, 15)},
    ],
    "fail_value": [
        {"year": 19999},  # Year out of range
        {"year": 2030, "month": 2, "day": 28, "hour": 14},  # hour with no minute
        {"year": 2030, "month": 20, "day": 28},  # month out of range
        {"year": 2030, "month": 2, "day": 30},  # day out of range
        {  # hour out of range
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 24,
            "minute": 0,
        },
        {  # minute out of range
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 23,
            "minute": 60,
        },
        {  # second out of range
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 23,
            "minute": 0,
            "second": 60,
        },
        {  # microsecond out of range
            "year": 2030,
            "month": 2,
            "day": 28,
            "hour": 23,
            "minute": 0,
            "second": 6,
            "microsecond": 1_999_999,
        },
        {"year": "2011-09-1212:14"},  # Missing spacer, fromisoformat fails
        {"year": 2021, "day": 13},  # No month
        {"year": 2021, "month": 2, "hour": 23, "minute": 59},  # No day
        {"year": 2021, "month": 2, "day": 28, "minute": 59},  # No hour
        {"year": 2021, "month": 2, "day": 28, "hour": 23},  # No Minute
        {"year": 2021, "month": 2, "day": 28, "tzinfo": timezone.utc},  # No time
    ],
}

# These tests only work on 3.7+
if sys.version_info.major == 3 and sys.version_info.minor > 6:
    cases["success"].extend(
        [
            {"year": "2011-09-12T12:14:31-06:00:05"},
            {
                "year": datetime(
                    2011,
                    9,
                    12,
                    12,
                    14,
                    31,
                    tzinfo=timezone(timedelta(hours=-6, seconds=5, microseconds=4321)),
                ).isoformat()
            },
            {
                "year": datetime(
                    2011,
                    9,
                    12,
                    12,
                    14,
                    31,
                    tzinfo=timezone(timedelta(hours=-6, seconds=5, microseconds=4321)),
                ).isoformat(timespec="milliseconds")
            },
        ]
    )


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
    """Test creation of a FhirDateTime from a native object, should fail."""
    FhirDateTime.from_native(param)


@pytest.mark.parametrize("params", cases["success"])
def test_creation(params: dict):
    """Test creation of a FhirDateTime object with given params."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_type"])
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_bad_creation_type(params: dict):
    """Test creation of a FhirDateTime object that should fail with TypeError."""
    make_and_assert(params)


@pytest.mark.parametrize("params", cases["fail_value"])
@pytest.mark.xfail(raises=ValueError, strict=True)
def test_bad_creation_value(params: dict):
    """Test creation of a FhirDateTime object that should fail with ValueError."""
    make_and_assert(params)


def test_getitem():
    """Test accessing an invalid index raises an error."""
    d = FhirDateTime(**random.choice(cases["success"]))
    min_ = 0
    max_ = 6
    for _ in range(100):
        with pytest.raises(IndexError):
            _ = d[random.randrange(min_ - 1, -2000, -1)]
        with pytest.raises(IndexError):
            _ = d[random.randrange(max_ + 1, 2000)]


def test_other_methods():
    """Test other methods, mostly for coverage."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, 295815, tzinfo=timezone.utc)
    assert dt.date() == date(2020, 5, 4)
    assert dt.time() == time(13, 42, 54, 295815)
    assert (dt - timedelta(5)) == FhirDateTime(
        2020, 4, 29, 13, 42, 54, 295815, tzinfo=timezone.utc
    )

    dt = dt.replace(tzinfo=timezone(timedelta(hours=3)))
    assert dt.timetz() == time(13, 42, 54, 295815, tzinfo=timezone(timedelta(hours=3)))
    assert dt.timetuple() == _time.struct_time((2020, 5, 4, 13, 42, 54, 0, 125, -1))

    assert dt.isoformat() == "2020-05-04T13:42:54.295815+03:00"
    assert dt.isoformat(timespec="milliseconds") == "2020-05-04T13:42:54.295+03:00"
    with pytest.raises(ValueError):
        dt.isoformat(timespec="doesn't exist")
    with pytest.raises(ValueError):
        FhirDateTime.fromisoformat("2020*02*13")

    assert dt.weekday() == 0
    assert dt.isoweekday() == 1
    assert dt.isocalendar() == (2020, 19, 1)

    assert dt.asdatetime == datetime(
        2020, 5, 4, 13, 42, 54, 295815, timezone(timedelta(hours=3))
    )
    assert dt.timestamp() == 1588588974.295815

    assert str(FhirDateTime("2020")) == "2020"
    assert str(FhirDateTime("2020-05")) == "2020-05"
    assert str(FhirDateTime("2020-05-04")) == "2020-05-04"

"""Test parameters of creating FhirDateTime objects."""

from __future__ import annotations

import random
import time as _time
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from fhirdatetime import FhirDateTime, __version__

if TYPE_CHECKING:
    from collections.abc import Callable

random.seed()


def test_version() -> None:
    """Check library version is what it should be."""
    ver = "0.2.0"
    assert __version__ == ver
    with Path("pyproject.toml").open() as proj:
        for line in proj:
            if line.startswith("version = "):
                assert line == f'version = "{ver}"\n'
                return
    msg = "Unable to find version string in pyproject.toml"
    raise ValueError(msg)


def compare_native(dt: FhirDateTime, other: date | datetime) -> None:
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


def make_and_assert(params: dict) -> None:
    """Create and run tests on a FhirDateTime object."""
    dt = FhirDateTime(**params)
    if isinstance(params["year"], (date, datetime)):
        compare_native(dt, params["year"])
        return

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


success_cases: list[dict] = [
    {"year": 2011},
    {"year": 1909, "month": 9},
    {"year": 30, "month": 2, "day": 28},
    {"year": 2030, "month": 2, "day": 28, "hour": 14, "minute": 54, "tzinfo": UTC},
    {
        "year": 2030,
        "month": 2,
        "day": 28,
        "hour": 23,
        "minute": 53,
        "second": 6,
        "microsecond": 999_999,  # Max value for microsecond
        "tzinfo": UTC,
    },
    {"year": datetime(2011, 9, 12, 14, 53, tzinfo=UTC)},
    {
        "year": datetime(
            2020,
            11,
            1,
            23,
            53,
            tzinfo=timezone(timedelta(hours=-6)),
            fold=1,
        ),
    },
    {"year": date(2011, 9, 12)},
    {"year": "2011"},
    {"year": "2011-09"},
    {"year": "2011-09-12"},
    {"year": "2011-09-12T12:14-06:00"},
    {"year": "2011-09-12T12:14:31-06:00"},
    {"year": "2016-01-26T21:58:41.000Z"},
]

fail_type_cases: list[dict] = [
    {"year": None},
    {"year": time(12, 15)},
    {"year": 2021, "month": 2.0},  # float instead of int
]

fail_value_cases: list[dict] = [
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
        "tzinfo": UTC,
    },
    {  # microsecond out of range
        "year": 2030,
        "month": 2,
        "day": 28,
        "hour": 23,
        "minute": 0,
        "second": 6,
        "microsecond": 1_999_999,
        "tzinfo": UTC,
    },
    {"year": "2011-09-1212:14"},  # Missing spacer, fromisoformat fails
    {"year": 2021, "day": 13},  # No month
    {"year": 2021, "month": 2, "hour": 23, "minute": 59},  # No day
    {"year": 2021, "month": 2, "day": 28, "minute": 59},  # No hour
    {"year": 2021, "month": 2, "day": 28, "hour": 23},  # No Minute
    {"year": 2021, "month": 2, "day": 28, "tzinfo": UTC},  # No time
    {"year": 2021, "month": 2, "day": 28, "hour": 23, "minute": 59},  # Time without tzinfo
    {"year": 2021, "month": 1, "day": 1, "fold": 2},  # fold out of range
]

success_cases.extend(
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
            ).isoformat(),
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
            ).isoformat(timespec="milliseconds"),
        },
    ],
)


@pytest.mark.parametrize(
    "param",
    [
        date.today().isoformat(),
        datetime.now(UTC).isoformat(),
        {"year": 2030, "month": 2, "day": 28, "hour": 14, "minute": 54},
        "2011-09-12T12:14:31-06:00",
    ],
)
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_from_native_xfail(param: str | dict) -> None:
    """Test creation of a FhirDateTime from a native object, should fail."""
    # param is deliberately never a `date`/`datetime` here -- that's the point
    # of this test (from_native must reject these types).
    FhirDateTime.from_native(param)  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize("params", success_cases)
def test_creation(params: dict) -> None:
    """Test creation of a FhirDateTime object with given params."""
    make_and_assert(params)


@pytest.mark.parametrize("params", fail_type_cases)
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_bad_creation_type(params: dict) -> None:
    """Test creation of a FhirDateTime object that should fail with TypeError."""
    make_and_assert(params)


@pytest.mark.parametrize("params", fail_value_cases)
@pytest.mark.xfail(raises=ValueError, strict=True)
def test_bad_creation_value(params: dict) -> None:
    """Test creation of a FhirDateTime object that should fail with ValueError."""
    make_and_assert(params)


def test_getitem() -> None:
    """Test accessing an invalid index raises an error."""
    d = FhirDateTime(**random.choice(success_cases))
    min_ = 0
    max_ = 6
    for _ in range(100):
        with pytest.raises(IndexError):
            _ = d[random.randrange(min_ - 1, -2000, -1)]
        with pytest.raises(IndexError):
            _ = d[random.randrange(max_ + 1, 2000)]


def test_other_methods() -> None:
    """Test other methods, mostly for coverage."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, 295815, tzinfo=UTC)
    assert dt.date() == date(2020, 5, 4)
    assert dt.time() == time(13, 42, 54, 295815)
    assert (dt - timedelta(5)) == FhirDateTime(
        2020,
        4,
        29,
        13,
        42,
        54,
        295815,
        tzinfo=UTC,
    )

    dt = dt.replace(tzinfo=timezone(timedelta(hours=3)))
    assert dt.timetz() == time(13, 42, 54, 295815, tzinfo=timezone(timedelta(hours=3)))
    assert dt.timetuple() == _time.struct_time((2020, 5, 4, 13, 42, 54, 0, 125, -1))

    assert dt.isoformat() == "2020-05-04T13:42:54.295815+03:00"
    assert dt.isoformat(timespec="milliseconds") == "2020-05-04T13:42:54.295+03:00"
    with pytest.raises(ValueError, match="Unknown timespec value"):
        dt.isoformat(timespec="doesn't exist")
    # No match=: the message comes from stdlib strptime's fallback path and its
    # exact text is Python-version-dependent (see TODO.md's 3.14 strptime note).
    with pytest.raises(ValueError):  # noqa: PT011
        FhirDateTime.fromisoformat("2020*02*13")

    assert dt.weekday() == 0
    assert dt.isoweekday() == 1
    assert dt.isocalendar() == (2020, 19, 1)

    assert dt.asdatetime == datetime(
        2020,
        5,
        4,
        13,
        42,
        54,
        295815,
        timezone(timedelta(hours=3)),
    )
    assert dt.timestamp() == 1588588974.295815

    assert str(FhirDateTime("2020")) == "2020"
    assert str(FhirDateTime("2020-05")) == "2020-05"
    assert str(FhirDateTime("2020-05-04")) == "2020-05-04"


def test_str_includes_time_portion() -> None:
    """str() on a time-bearing FhirDateTime must include the time, not just the date.

    Regression test for an MRO-shadowing bug found during the core-class
    design review: FhirDate binds `__str__ = isoformat` directly to its
    own (date-only) function object. Since FhirDate precedes _DateTime in
    FhirDateTime's MRO, that alias would shadow _DateTime.__str__'s
    polymorphic `self.isoformat(sep=" ")` call for any FhirDateTime that
    didn't explicitly override __str__ itself -- silently truncating the
    time portion. FhirDateTime now has its own explicit __str__; this
    guards against that regressing silently again.
    """
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    assert str(dt) == dt.isoformat(sep=" ")
    assert str(dt) == "2020-05-04 13:42:54+00:00"

    # Date-only is unaffected either way (no time to truncate).
    assert str(FhirDateTime(2020, 5, 4)) == "2020-05-04"


def test_isocalendar_fields() -> None:
    """isocalendar() returns a named-tuple-like object with named attribute access."""
    dt = FhirDateTime(2020, 5, 4)
    ic = dt.isocalendar()
    assert ic.year == 2020
    assert ic.week == 19
    assert ic.weekday == 1
    assert repr(ic) == "IsoCalendarDate(year=2020, week=19, weekday=1)"


def test_leap_second_normalized_to_59_on_parse() -> None:
    """fromisoformat() accepts a FHIR-legal leap second (:60) by normalizing it to :59.

    FHIR's dateTime grammar explicitly allows a leap second, but this
    library never produces one -- per FHIR's own guidance ("applications
    reading times SHOULD accept and handle leap seconds gracefully, and
    applications producing them MAY choose to avoid encoding leap
    seconds"). Direct construction still rejects second=60 outright; only
    parsing normalizes it.
    """
    # Numeric-offset path (vendored _DateTime.fromisoformat).
    assert FhirDateTime.fromisoformat("2015-06-30T23:59:60+00:00") == FhirDateTime(2015, 6, 30, 23, 59, 59, tzinfo=UTC)
    # Z-literal path (the strptime-based fallback).
    assert FhirDateTime.fromisoformat("2015-06-30T23:59:60Z") == FhirDateTime(2015, 6, 30, 23, 59, 59, tzinfo=UTC)
    # Fractional seconds preserved through normalization.
    leap_with_fraction = FhirDateTime.fromisoformat("2015-06-30T23:59:60.5Z")
    assert leap_with_fraction.second == 59
    assert leap_with_fraction.microsecond == 500_000
    # A normal :59 is left alone (not a false-positive match).
    assert FhirDateTime.fromisoformat("2015-06-30T23:59:59Z") == FhirDateTime(2015, 6, 30, 23, 59, 59, tzinfo=UTC)

    with pytest.raises(ValueError, match=r"second must be in 0\.\.59"):
        FhirDateTime(2015, 6, 30, 23, 59, 60, tzinfo=UTC)


def test_offset_with_seconds_in_isoformat() -> None:
    """isoformat() renders a UTC offset with non-zero seconds/microseconds."""
    tz = timezone(timedelta(hours=-6, seconds=5))
    dt = FhirDateTime(2011, 9, 12, 12, 14, 31, tzinfo=tz)
    assert dt.isoformat() == "2011-09-12T12:14:31-05:59:55"

    tz_us = timezone(timedelta(hours=1, microseconds=250_000))
    dt_us = FhirDateTime(2011, 9, 12, 12, 14, 31, tzinfo=tz_us)
    assert dt_us.isoformat() == "2011-09-12T12:14:31+01:00:00.250000"


def test_tzname() -> None:
    """tzname() reflects the tzinfo attached to the instance.

    No naive-instance case: a time-bearing FhirDateTime always has a tzinfo
    now (FHIR requires it), so tzname()'s "no tzinfo -> None" branch is only
    reachable via a date-only instance, which has no tzname() concept at all.
    """
    assert FhirDateTime(2020, 1, 1, 0, 0, tzinfo=UTC).tzname() == "UTC"


def test_strftime_and_format() -> None:
    """strftime() and format()/__format__() delegate correctly."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    assert dt.strftime("%Y-%m-%d %H:%M:%S %z") == "2020-05-04 13:42:54 +0000"
    assert format(dt, "%Y/%m/%d") == "2020/05/04"
    assert format(dt, "") == str(dt)
    with pytest.raises(TypeError):
        dt.__format__(5)  # type: ignore[arg-type]


def test_ctime() -> None:
    """ctime() produces the classic ctime()-style string."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    assert dt.ctime() == "Mon May  4 13:42:54 2020"


def test_from_native() -> None:
    """from_native() builds a FhirDateTime from a real date/datetime."""
    d = date(2011, 9, 12)
    dt_native = datetime(2011, 9, 12, 14, 53, 12, 123456, tzinfo=UTC)

    from_d = FhirDateTime.from_native(d)
    assert isinstance(from_d, FhirDateTime)
    assert (from_d.year, from_d.month, from_d.day) == (2011, 9, 12)
    assert from_d.hour is None

    from_dt = FhirDateTime.from_native(dt_native)
    assert isinstance(from_dt, FhirDateTime)
    compare_native(from_dt, dt_native)


def test_tz_required_whenever_time_present() -> None:
    """FHIR requires a timezone whenever a time is specified, enforced on every path.

    Explicit-field construction goes through `_check_time_fields`; copying
    from an existing naive real `datetime` (whether via `__init__`,
    `from_native`, `now()`, or `fromtimestamp()`) goes through the separate
    `_replace_with` check instead -- both need covering, since fixing one
    doesn't fix the other.
    """
    # Explicit fields, via _check_time_fields.
    with pytest.raises(ValueError, match="requires a timezone"):
        FhirDateTime(2021, 3, 15, 23, 56)

    # Date-only construction is unaffected: no time means no tz requirement.
    assert FhirDateTime(2021, 3, 15).tzinfo is None

    # Copying from an existing naive real datetime, via _replace_with.
    naive_native = datetime(2021, 3, 15, 23, 56)
    with pytest.raises(ValueError, match="requires a timezone"):
        FhirDateTime(naive_native)
    with pytest.raises(ValueError, match="requires a timezone"):
        FhirDateTime.from_native(naive_native)

    # Copying from a naive real date (no time at all) is unaffected.
    assert FhirDateTime(date(2021, 3, 15)).tzinfo is None


def test_repr() -> None:
    """__repr__ trims unset trailing fields and appends tzinfo/fold when set.

    No naive time-bearing case (e.g. hour/minute set, no tzinfo, no fold):
    a time-bearing FhirDateTime always has a tzinfo now, so that combination
    can't be constructed. The "no tzinfo" trimming branch is still exercised
    by the date-only cases below, where tzinfo is never applicable anyway.
    """
    assert repr(FhirDateTime(2020)) == "fhirdatetime.FhirDateTime(2020)"
    assert repr(FhirDateTime(2020, 5, 4)) == "fhirdatetime.FhirDateTime(2020, 5, 4)"
    assert (
        repr(FhirDateTime(2020, 5, 4, 13, 42, tzinfo=UTC))
        == "fhirdatetime.FhirDateTime(2020, 5, 4, 13, 42, tzinfo=datetime.timezone.utc)"
    )
    assert (
        repr(FhirDateTime(2020, 5, 4, 13, 42, tzinfo=UTC, fold=1))
        == "fhirdatetime.FhirDateTime(2020, 5, 4, 13, 42, tzinfo=datetime.timezone.utc, fold=1)"
    )


def test_hash() -> None:
    """__hash__ is consistent with __eq__ and usable in sets/dicts."""
    a = FhirDateTime(2020)
    b = FhirDateTime(2020, 9, 1)  # Equal to `a` under FhirDateTime's ambiguous-field ==
    c = FhirDateTime(2021, 5, 4)

    assert a == b
    assert hash(a) == hash(b)
    assert hash(a) == hash(2020)

    s = {a}
    assert b in s  # Equal objects must land in the same hash bucket
    assert c not in s

    d = {a: "first"}
    d[b] = "second"
    assert d == {a: "second"}  # b overwrote a's entry, since a == b


def test_ne_incompatible_type() -> None:
    """__ne__ defers via NotImplemented for non-date/datetime types."""
    assert FhirDateTime(2021) != {2021}
    assert FhirDateTime(2021) != 5
    assert FhirDateTime(2021) != "2021"


@pytest.mark.parametrize(
    "op",
    [
        lambda a, b: a < b,
        lambda a, b: a <= b,
        lambda a, b: a > b,
        lambda a, b: a >= b,
    ],
)
def test_ordering_incompatible_type_raises(op: Callable[[object, object], bool]) -> None:
    """Ordering comparisons against a non-date/datetime type raise TypeError."""
    with pytest.raises(TypeError, match="Cannot compare FhirDateTime"):
        op(FhirDateTime(2021), "not a date")


def test_sort_key_bad_attr_path() -> None:
    """sort_key()'s attr-path callable raises when the path leads elsewhere."""
    key = FhirDateTime.sort_key("value")
    with pytest.raises(TypeError, match="attr_path must lead to an instance of FhirDateTime"):
        key(SimpleNamespace(value=42))

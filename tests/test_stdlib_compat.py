"""Tests for FhirDateTime's compatibility with the standard datetime API.

These exercise the vendored `_DateTime` base (`fhirdatetime/_datetime.py`)
through FhirDateTime's public surface: construction from timestamps,
timezone conversion, arithmetic, string formatting, and pickling. Methods
that FhirDateTime overrides outright (comparison operators, `_cmp`,
`isoformat`, `__repr__`, `__hash__`) are exercised in test_fhirdatetime.py
and test_compare.py instead, since `_DateTime`'s own versions of those are
unreachable dead code for FhirDateTime instances.
"""

from __future__ import annotations

import copy
import pickle
import warnings
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo

import pytest

from fhirdatetime import FhirDateTime


def test_pickle_round_trip_full_precision() -> None:
    """A fully-specified, timezone-aware instance survives pickling."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, 295815, tzinfo=UTC)
    restored = pickle.loads(pickle.dumps(dt))  # noqa: S301
    assert restored == dt
    assert isinstance(restored, FhirDateTime)
    assert restored.tzinfo == UTC


@pytest.mark.parametrize(
    "dt",
    [
        FhirDateTime(2021),
        FhirDateTime(2021, 4),
        FhirDateTime(2021, 4, 12),
        FhirDateTime(2021, 4, 12, 8, 30),
        FhirDateTime(2021, 4, 12, 8, 30, tzinfo=timezone(timedelta(hours=-6))),
    ],
)
def test_pickle_round_trip_partial_precision(dt: FhirDateTime) -> None:
    """Partial-precision instances (FHIR's whole point) also round-trip."""
    restored = pickle.loads(pickle.dumps(dt))  # noqa: S301
    assert restored == dt
    assert restored.month == dt.month
    assert restored.hour == dt.hour
    assert restored.tzinfo == dt.tzinfo


def test_deepcopy() -> None:
    """copy.deepcopy uses the same __reduce_ex__ path as pickle."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    dup = copy.deepcopy(dt)
    assert dup == dt
    assert dup is not dt
    assert isinstance(dup, FhirDateTime)


def test_strftime() -> None:
    """strftime() delegates to the vendored _wrap_strftime helper."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    assert dt.strftime("%Y-%m-%d") == "2020-05-04"
    assert dt.strftime("%H:%M:%S %z %Z") == "13:42:54 +0000 UTC"


def test_ctime() -> None:
    """ctime() produces the classic ctime()-style string."""
    assert FhirDateTime(2020, 5, 4, 13, 42, 54).ctime() == "Mon May  4 13:42:54 2020"


def test_combine() -> None:
    """combine() builds a FhirDateTime from a date and a time."""
    combined = FhirDateTime.combine(date(2020, 1, 2), time(5, 6, 7, 8, tzinfo=UTC))
    assert isinstance(combined, FhirDateTime)
    assert combined == FhirDateTime(2020, 1, 2, 5, 6, 7, 8, tzinfo=UTC)


def test_combine_rejects_wrong_argument_types() -> None:
    """combine() type-checks its `date` and `time` arguments."""
    with pytest.raises(TypeError, match="date argument must be a date instance"):
        FhirDateTime.combine("not a date", time(5, 6))

    with pytest.raises(TypeError, match="time argument must be a time instance"):
        FhirDateTime.combine(date(2020, 1, 2), "not a time")


def test_replace_preserves_tzinfo_by_default() -> None:
    """replace() without a `tzinfo` argument keeps the original tzinfo."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, tzinfo=UTC)
    moved = dt.replace(year=2021)
    assert moved.tzinfo == UTC
    assert moved.year == 2021


def test_fromtimestamp_naive() -> None:
    """fromtimestamp() without a tz matches native datetime.fromtimestamp()."""
    ts = 1_588_599_774.295815
    fhir = FhirDateTime.fromtimestamp(ts)
    native = datetime.fromtimestamp(ts)
    assert (fhir.year, fhir.month, fhir.day, fhir.hour, fhir.minute, fhir.second) == (
        native.year,
        native.month,
        native.day,
        native.hour,
        native.minute,
        native.second,
    )
    assert fhir.tzinfo is None


@pytest.mark.parametrize("tz", [UTC, timezone(timedelta(hours=5)), timezone(timedelta(hours=-6))])
def test_fromtimestamp_aware(tz: timezone) -> None:
    """fromtimestamp() with a tz produces a correctly-offset, aware instance.

    Regression test: this used to raise `ValueError: fromutc: dt.tzinfo is
    not self`, because the vendored fold-detection path called
    `tz.fromutc()`, which reads `tzinfo` off the C-level `datetime` struct
    rather than through this class's Python `tzinfo` property.
    """
    ts = 1_588_599_774.295815
    fhir = FhirDateTime.fromtimestamp(ts, tz=tz)
    native = datetime.fromtimestamp(ts, tz=tz)
    assert fhir == native
    assert fhir.tzinfo == tz


def test_utcfromtimestamp() -> None:
    """utcfromtimestamp() produces a naive UTC instance."""
    ts = 1_588_599_774.295815
    fhir = FhirDateTime.utcfromtimestamp(ts)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        native = datetime.utcfromtimestamp(ts)  # ty: ignore[deprecated]
    assert (fhir.year, fhir.month, fhir.day, fhir.hour, fhir.minute, fhir.second) == (
        native.year,
        native.month,
        native.day,
        native.hour,
        native.minute,
        native.second,
    )
    assert fhir.tzinfo is None


def test_now_and_utcnow() -> None:
    """now()/now(tz)/utcnow() return sane, current FhirDateTime instances."""
    before = datetime.now(UTC)
    naive = FhirDateTime.now()
    aware = FhirDateTime.now(UTC)
    utc_now = FhirDateTime.utcnow()
    after = datetime.now(UTC)

    assert isinstance(naive, FhirDateTime)
    assert naive.tzinfo is None
    assert aware.tzinfo == UTC
    assert before <= aware <= after
    assert before.replace(tzinfo=None) <= utc_now <= after.replace(tzinfo=None)


def test_naive_timestamp_matches_native() -> None:
    """timestamp() on a naive instance goes through the vendored _mktime()."""
    fhir = FhirDateTime(2020, 5, 4, 13, 42, 54, 295815)
    native = datetime(2020, 5, 4, 13, 42, 54, 295815)
    assert fhir.timestamp() == native.timestamp()


def test_astimezone() -> None:
    """astimezone() converts to another timezone, preserving the instant."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, 295815, tzinfo=UTC)
    converted = dt.astimezone(timezone(timedelta(hours=5)))
    assert converted == dt
    assert converted.tzinfo == timezone(timedelta(hours=5))
    assert converted.hour == 18


def test_add_and_radd() -> None:
    """`+` between a FhirDateTime and a timedelta works in both operand orders."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    expected = FhirDateTime(2020, 5, 5, 13, 42, 54, tzinfo=UTC)
    assert dt + timedelta(days=1) == expected
    assert timedelta(days=1) + dt == expected


def test_add_incompatible_type() -> None:
    """`+` with a non-timedelta right-hand side defers via NotImplemented."""
    with pytest.raises(TypeError):
        FhirDateTime(2020, 5, 4) + "not a timedelta"


def test_sub_incompatible_type() -> None:
    """`-` with a type that's neither a timedelta nor a datetime-like raises."""
    with pytest.raises(TypeError):
        FhirDateTime(2020, 5, 4) - "not a timedelta or datetime"


def test_sub_equal_offset_different_tzinfo_objects() -> None:
    """Subtraction compares UTC offsets, not tzinfo identity."""
    a = FhirDateTime(2020, 5, 4, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    b = FhirDateTime(2020, 5, 4, 10, 0, tzinfo=timezone(timedelta(hours=2, seconds=0)))
    assert a - b == timedelta(hours=2)


def test_sub_naive_and_aware_raises() -> None:
    """Subtracting a naive instance from an aware one is a TypeError."""
    aware = FhirDateTime(2020, 5, 4, 12, 0, tzinfo=UTC)
    naive = FhirDateTime(2020, 5, 4, 10, 0)
    with pytest.raises(TypeError, match="cannot mix naive and timezone-aware time"):
        _ = aware - naive


def test_utctimetuple() -> None:
    """utctimetuple() shifts to UTC before building the struct_time."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=timezone(timedelta(hours=5)))
    tt = dt.utctimetuple()
    assert (tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec) == (
        2020,
        5,
        4,
        8,
        42,
        54,
    )


def test_timetuple_with_dst_aware_tzinfo() -> None:
    """timetuple()'s dst flag reflects a tzinfo that actually reports DST."""

    class _DstTz(tzinfo):
        def utcoffset(self, _dt: object, /) -> timedelta:
            return timedelta(hours=1)

        def dst(self, _dt: object, /) -> timedelta:
            return timedelta(hours=1)

        def tzname(self, _dt: object, /) -> str:
            return "DST"

    class _NoDstTz(_DstTz):
        def dst(self, _dt: object, /) -> timedelta:
            return timedelta(0)

    dt = FhirDateTime(2020, 7, 4, 13, 42, 54, tzinfo=_DstTz())
    assert dt.timetuple().tm_isdst == 1

    dt_zero_dst = FhirDateTime(2020, 7, 4, 13, 42, 54, tzinfo=_NoDstTz())
    assert dt_zero_dst.timetuple().tm_isdst == 0

    dt_unknown_dst = FhirDateTime(2020, 7, 4, 13, 42, 54, tzinfo=UTC)
    assert dt_unknown_dst.timetuple().tm_isdst == -1


def test_dst_and_timetuple_on_naive_instance() -> None:
    """dst()/timetuple() on a naive (no tzinfo) instance short-circuit to None/-1."""
    dt = FhirDateTime(2020, 7, 4, 13, 42, 54)
    assert dt.dst() is None
    assert dt.timetuple().tm_isdst == -1


def test_strftime_all_format_codes() -> None:
    """strftime()/%f/%z/%Z cover the microsecond, offset-sign, and offset-precision branches."""
    dt = FhirDateTime(2020, 5, 4, 13, 42, 54, 123456, tzinfo=timezone(timedelta(hours=-5)))
    assert dt.strftime("%f") == "123456"
    assert dt.strftime("%z") == "-0500"  # Negative-offset branch

    dt_sec = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=timezone(timedelta(hours=1, minutes=2, seconds=3)))
    assert dt_sec.strftime("%z") == "+010203"  # Seconds-precision offset branch

    dt_us = FhirDateTime(
        2020,
        5,
        4,
        13,
        42,
        54,
        tzinfo=timezone(timedelta(hours=1, microseconds=500_000)),
    )
    assert dt_us.strftime("%z") == "+010000.500000"  # Microsecond-precision offset branch

    naive = FhirDateTime(2020, 5, 4, 13, 42, 54)
    assert naive.strftime("%z") == ""
    assert naive.strftime("%Z") == ""
    assert naive.strftime("100%") == "100%"  # Trailing bare '%' at end of format string


def test_isocalendar_date_pickle() -> None:
    """The IsoCalendarDate returned by isocalendar() pickles as a plain tuple."""
    ic = FhirDateTime(2020, 5, 4).isocalendar()
    restored = pickle.loads(pickle.dumps(ic))  # noqa: S301
    assert restored == tuple(ic)
    assert type(restored) is tuple


def test_astimezone_branches() -> None:
    """astimezone() with no arg, a same tz, and an invalid tz argument."""
    aware = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC)
    assert aware.astimezone(UTC) is aware  # Shortcut when target tz is already self's tz

    with pytest.raises(TypeError, match="tz argument must be an instance of tzinfo"):
        aware.astimezone("not a tzinfo")

    naive = FhirDateTime(2020, 5, 4, 13, 42, 54)
    local = naive.astimezone()  # No arg: converts using the system local timezone
    expected = datetime(2020, 5, 4, 13, 42, 54).astimezone()
    assert local.utcoffset() == expected.utcoffset()
    assert local.tzname() == expected.tzname()

    # No arg on an already-aware instance: still resolves the *system* local
    # timezone (not a no-op), exercising `_local_timezone`'s aware-self path.
    already_aware = FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=timezone(timedelta(hours=9)))
    local_from_aware = already_aware.astimezone()
    assert local_from_aware == already_aware
    assert local_from_aware.utcoffset() == expected.utcoffset()


def test_check_int_field_custom_objects() -> None:
    """Fields accept anything with __index__, and warn (but accept) on bare __int__."""

    class _Indexable:
        def __index__(self) -> int:
            return 6

    class _IntOnly:
        def __int__(self) -> int:
            return 6

    assert FhirDateTime(2020, _Indexable()).month == 6  # ty: ignore[invalid-argument-type]

    with pytest.deprecated_call():
        dt = FhirDateTime(2020, _IntOnly())  # ty: ignore[invalid-argument-type]
    assert dt.month == 6


def test_bad_tzinfo_implementations_are_rejected() -> None:
    """A tzinfo whose methods return the wrong type/range surfaces clear errors."""

    class _BadOffset(tzinfo):
        def utcoffset(self, _dt: object, /) -> timedelta:
            return timedelta(hours=48)  # Out of the valid +/-24h range

        def dst(self, _dt: object, /) -> None:
            return None

        def tzname(self, _dt: object, /) -> None:
            return None

    class _WrongOffsetType(tzinfo):
        def utcoffset(self, _dt: object, /) -> int:  # ty: ignore[invalid-method-override]
            return 5

        def dst(self, _dt: object, /) -> None:
            return None

        def tzname(self, _dt: object, /) -> None:
            return None

    class _BadTzname(tzinfo):
        def utcoffset(self, _dt: object, /) -> None:
            return None

        def dst(self, _dt: object, /) -> None:
            return None

        def tzname(self, _dt: object, /) -> int:  # ty: ignore[invalid-method-override]
            return 5

    with pytest.raises(ValueError, match="must be strictly between"):
        FhirDateTime(2020, 5, 4, 1, 1, tzinfo=_BadOffset()).utcoffset()

    with pytest.raises(TypeError, match="utcoffset"):
        FhirDateTime(2020, 5, 4, 1, 1, tzinfo=_WrongOffsetType()).utcoffset()

    with pytest.raises(TypeError, match="tzname"):
        FhirDateTime(2020, 5, 4, 1, 1, tzinfo=_BadTzname()).tzname()


def test_tzinfo_arg_type_checked() -> None:
    """fromtimestamp() rejects a `tz` argument that isn't a tzinfo instance."""
    with pytest.raises(TypeError, match="tzinfo argument must be None or of a tzinfo subclass"):
        FhirDateTime.fromtimestamp(0, tz="not a tzinfo")  # ty: ignore[invalid-argument-type]

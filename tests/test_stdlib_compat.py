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
        FhirDateTime(2021, 4, 12, 8, 30, tzinfo=UTC),
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
    assert FhirDateTime(2020, 5, 4, 13, 42, 54, tzinfo=UTC).ctime() == "Mon May  4 13:42:54 2020"


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


def test_fromtimestamp_without_tz_raises() -> None:
    """fromtimestamp() with no `tz` argument would produce a naive instance -- now an error.

    FHIR requires a timezone whenever a time is present, enforced on every
    construction path, including this one (`from_native` -> `_replace_with`).
    """
    with pytest.raises(ValueError, match="requires a timezone"):
        FhirDateTime.fromtimestamp(1_588_599_774.295815)


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


def test_utcfromtimestamp_is_utc_aware() -> None:
    """utcfromtimestamp() attaches UTC tzinfo, unlike stdlib's deprecated naive version.

    Unlike `fromtimestamp()`, there's no `tz` argument for a caller to fix a
    naive result with, and FHIR requires a timezone whenever a time is
    present -- so this overrides the vendored/stdlib "naive by convention"
    behavior rather than leaving it permanently unusable.
    """
    ts = 1_588_599_774.295815
    fhir = FhirDateTime.utcfromtimestamp(ts)
    assert fhir.tzinfo == UTC
    assert fhir == FhirDateTime.fromtimestamp(ts, tz=UTC)


def test_now_and_utcnow() -> None:
    """now(tz) returns a sane, current, aware FhirDateTime instance; utcnow() attaches UTC.

    now() without a `tz` argument still raises -- unlike utcnow(), it has a
    `tz` parameter a caller could have supplied, so silently defaulting it
    would mask a likely mistake rather than fix an unusable method.
    """
    before = datetime.now(UTC)
    aware = FhirDateTime.now(UTC)
    utc_now = FhirDateTime.utcnow()
    after = datetime.now(UTC)

    assert isinstance(aware, FhirDateTime)
    assert aware.tzinfo == UTC
    assert before <= aware <= after
    assert utc_now.tzinfo == UTC
    assert before <= utc_now <= after

    with pytest.raises(ValueError, match="requires a timezone"):
        FhirDateTime.now()


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
        FhirDateTime(2020, 5, 4) + "not a timedelta"  # ty: ignore[unsupported-operator]


def test_sub_incompatible_type() -> None:
    """`-` with a type that's neither a timedelta nor a datetime-like raises."""
    with pytest.raises(TypeError):
        FhirDateTime(2020, 5, 4) - "not a timedelta or datetime"  # ty: ignore[unsupported-operator]


@pytest.mark.parametrize(
    "dt",
    [
        FhirDateTime(2021),
        FhirDateTime(2021, 4),
        FhirDateTime(2021, 4, 12),  # date complete, but no hour/minute
    ],
)
def test_arithmetic_on_partial_precision_raises(dt: FhirDateTime) -> None:
    """+/- on a partial-precision FhirDateTime raises a clear error.

    Without the `_require_full_precision` guard, this used to surface as a
    confusing internal `TypeError` from deep inside `toordinal`/`timedelta`
    (missing fields are `None`, not `0`) instead of an actionable message.
    """
    with pytest.raises(TypeError, match="unpopulated"):
        _ = dt + timedelta(days=1)
    with pytest.raises(TypeError, match="unpopulated"):
        _ = dt - FhirDateTime(2020, 5, 4, 12, 0, tzinfo=UTC)
    with pytest.raises(TypeError, match="unpopulated"):
        _ = FhirDateTime(2020, 5, 4, 12, 0, tzinfo=UTC) - dt


def test_min_max_are_fhirdatetime_instances() -> None:
    """FhirDateTime.min/.max must be FhirDateTime instances.

    Same rationale as `test_min_max_are_fhirdate_instances` in
    test_fhirdate.py -- without an explicit override, `.min`/`.max` would
    resolve via inheritance first to `FhirDate.min`/`.max`, then to the
    vendored `_DateTime.min`/`.max`, neither of which is a FhirDateTime.
    """
    assert isinstance(FhirDateTime.min, FhirDateTime)
    assert isinstance(FhirDateTime.max, FhirDateTime)
    assert FhirDateTime.min == FhirDateTime(1, 1, 1, 0, 0, tzinfo=UTC)
    assert FhirDateTime.max == FhirDateTime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)


def test_rsub_real_datetime_minus_fhir_datetime() -> None:
    """`real_datetime - fhir_datetime` must go through FhirDateTime's own __sub__.

    Same rationale as `test_rsub_real_date_minus_fhir_date` in
    test_fhirdate.py: without `__rsub__`, `datetime.__sub__`'s C
    implementation reads the frozen `(1, 1, 1)` placeholder struct instead
    of this instance's real values, silently computing a wrong timedelta.
    """
    real = datetime(2020, 5, 10, 12, 0, tzinfo=UTC)
    fhir = FhirDateTime(2020, 5, 4, 6, 0, tzinfo=UTC)
    assert real - fhir == timedelta(days=6, hours=6)


def test_sub_equal_offset_different_tzinfo_objects() -> None:
    """Subtraction compares UTC offsets, not tzinfo identity."""
    a = FhirDateTime(2020, 5, 4, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    b = FhirDateTime(2020, 5, 4, 10, 0, tzinfo=timezone(timedelta(hours=2, seconds=0)))
    assert a - b == timedelta(hours=2)


def test_sub_naive_and_aware_raises() -> None:
    """Subtracting a naive instance from an aware one is a TypeError.

    Uses a real naive `datetime` as the naive side, not a naive
    `FhirDateTime` -- the latter can no longer be constructed at all, since
    FHIR requires a timezone whenever a time is present. This still
    exercises the same naive/aware-mixing check in `_DateTime.__sub__`.
    """
    aware = FhirDateTime(2020, 5, 4, 12, 0, tzinfo=UTC)
    naive = datetime(2020, 5, 4, 10, 0)
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

    # No naive case: %z/%Z returning "" for a naive instance is now dead code
    # -- a time-bearing FhirDateTime always has a tzinfo. This still covers
    # the trailing-bare-'%' format-string edge case, just on an aware instance.
    assert dt.strftime("100%") == "100%"


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

    # No naive case: `_local_timezone`'s naive-self branch is now dead code
    # -- a time-bearing FhirDateTime always has a tzinfo. No-arg astimezone()
    # is still exercised below, on an already-aware instance.
    expected = datetime(2020, 5, 4, 13, 42, 54, tzinfo=UTC).astimezone()

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

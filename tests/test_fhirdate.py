"""Test parameters of creating FhirDate objects."""

import copy
import pickle
import random
import time as _time
from datetime import UTC, date, datetime, time, timedelta

import pytest

from fhirdatetime import FhirDate

random.seed()


def compare_native(d: FhirDate, other: date) -> None:
    """Check values when obj is created from a native type."""
    assert d.year == other.year
    assert d.month == other.month
    assert d.day == other.day


def make_and_assert(params: dict) -> None:
    """Create and run tests on a FhirDate object."""
    d = FhirDate(**params)
    if isinstance(params["year"], date):
        compare_native(d, params["year"])
        return

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


success_cases: list[dict] = [
    {"year": 2011},
    {"year": 1909, "month": 9},
    {"year": 30, "month": 2, "day": 28},
    {"year": date(2011, 9, 12)},
    {"year": "2011"},
    {"year": "2011-09"},
    {"year": "2011-09-12"},
]

fail_type_cases: list[dict] = [
    {"year": None},
    {"year": time(12, 15)},
    {"year": 2021, "month": 2, "day": 28, "tzinfo": UTC},  # No time
]

fail_value_cases: list[dict] = [
    {"year": 19999},  # Year out of range
    {"year": 2030, "month": 20, "day": 28},  # month out of range
    {"year": 2030, "month": 2, "day": 30},  # day out of range
    {"year": 2021, "day": 13},  # No month
]


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
    """Test creation of a FhirDate from a native object, should fail."""
    # param is deliberately never a `date` here -- that's the point of this
    # test (from_native must reject these types).
    FhirDate.from_native(param)  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize("params", success_cases)
def test_creation(params: dict) -> None:
    """Test creation of a FhirDate object with given params."""
    make_and_assert(params)


@pytest.mark.parametrize("params", fail_type_cases)
@pytest.mark.xfail(raises=TypeError, strict=True)
def test_bad_creation_type(params: dict) -> None:
    """Test creation of a FhirDate object that should fail with TypeError."""
    make_and_assert(params)


@pytest.mark.parametrize("params", fail_value_cases)
@pytest.mark.xfail(raises=ValueError, strict=True)
def test_bad_creation_value(params: dict) -> None:
    """Test creation of a FhirDate object that should fail with ValueError."""
    make_and_assert(params)


def test_getitem() -> None:
    """Test accessing an invalid index raises an error."""
    d = FhirDate(**random.choice(success_cases))
    min_ = 0
    max_ = 2
    for _ in range(100):
        with pytest.raises(IndexError):
            _ = d[random.randrange(min_ - 1, -2000, -1)]
        with pytest.raises(IndexError):
            _ = d[random.randrange(max_ + 1, 2000)]


def test_other_methods() -> None:
    """Test other methods, mostly for coverage."""
    d = FhirDate(2020, 5, 4)

    assert d.timetuple() == _time.struct_time((2020, 5, 4, 0, 0, 0, 0, 125, -1))

    assert d.isoformat() == "2020-05-04"
    with pytest.raises(ValueError, match="Unknown date format"):
        FhirDate.fromisoformat("2020*02*13")

    assert d.weekday() == 0
    assert d.isoweekday() == 1
    assert d.isocalendar() == (2020, 19, 1)

    assert str(FhirDate("2020")) == "2020"
    assert str(FhirDate("2020-05")) == "2020-05"
    assert str(FhirDate("2020-05-04")) == "2020-05-04"


def test_pickle_round_trip_full_precision() -> None:
    """A fully-specified instance survives pickling."""
    d = FhirDate(2020, 5, 4)
    restored = pickle.loads(pickle.dumps(d))  # noqa: S301
    assert restored == d
    assert isinstance(restored, FhirDate)


@pytest.mark.parametrize("d", [FhirDate(2021), FhirDate(2021, 4), FhirDate(2021, 4, 12)])
def test_pickle_round_trip_partial_precision(d: FhirDate) -> None:
    """Partial-precision instances (FHIR's whole point) also round-trip."""
    restored = pickle.loads(pickle.dumps(d))  # noqa: S301
    assert restored == d
    assert restored.month == d.month


def test_deepcopy() -> None:
    """copy.deepcopy uses the same __reduce_ex__ path as pickle."""
    d = FhirDate(2020, 5, 4)
    dup = copy.deepcopy(d)
    assert dup == d
    assert dup is not d
    assert isinstance(dup, FhirDate)


def test_copy() -> None:
    """copy.copy uses the same __reduce_ex__ path as pickle."""
    d = FhirDate(2020, 5, 4)
    dup = copy.copy(d)
    assert dup == d
    assert dup is not d
    assert isinstance(dup, FhirDate)


def test_add_and_radd() -> None:
    """`+` between a full-precision FhirDate and a timedelta works in both operand orders."""
    d = FhirDate(2020, 5, 4)
    expected = FhirDate(2020, 5, 5)
    assert d + timedelta(days=1) == expected
    assert timedelta(days=1) + d == expected


def test_sub_date() -> None:
    """`-` between two full-precision FhirDate instances returns a timedelta."""
    assert FhirDate(2020, 5, 5) - FhirDate(2020, 5, 4) == timedelta(days=1)


def test_min_max_are_fhirdate_instances() -> None:
    """FhirDate.min/.max must be FhirDate instances, not the private vendored _Date.

    Without an explicit override, these would resolve via inheritance to
    `_Date.min`/`.max` (set at the bottom of `_datetime.py`) -- a leaked
    private type where `isinstance(FhirDate.min, FhirDate)` is `False`.
    """
    assert isinstance(FhirDate.min, FhirDate)
    assert isinstance(FhirDate.max, FhirDate)
    assert FhirDate.min == FhirDate(1, 1, 1)
    assert FhirDate.max == FhirDate(9999, 12, 31)


def test_rsub_real_date_minus_fhir_date() -> None:
    """`real_date - fhir_date` must go through FhirDate's own __sub__, not date's C fast path.

    Without `__rsub__`, `date.__sub__`'s C implementation reads the other
    operand's year/month/day directly off its C struct once it confirms
    the operand is date-like -- since FhirDate's real struct is frozen at
    the `__new__` placeholder (1, 1, 1), that silently computed a *wrong*
    timedelta (based on the placeholder, not the actual value) instead of
    raising. This must never regress silently, so assert the exact value,
    not just that it doesn't crash.
    """
    real = date(2020, 5, 10)
    fhir = FhirDate(2020, 5, 4)
    assert real - fhir == timedelta(days=6)
    # Also confirm it's not coincidentally right for one value only.
    assert date(1999, 1, 1) - FhirDate(1998, 1, 1) == timedelta(days=365)


@pytest.mark.parametrize("d", [FhirDate(2021), FhirDate(2021, 4)])
def test_arithmetic_on_partial_precision_raises(d: FhirDate) -> None:
    """+/- on a partial-precision FhirDate raises a clear error, not an internal TypeError."""
    with pytest.raises(TypeError, match="unpopulated month/day"):
        _ = d + timedelta(days=1)
    with pytest.raises(TypeError, match="unpopulated month/day"):
        _ = d - FhirDate(2020, 5, 4)
    with pytest.raises(TypeError, match="unpopulated month/day"):
        _ = FhirDate(2020, 5, 4) - d

# -*- coding: utf-8 -*-
"""Functions pulled from the standard library from Python 3.9.1.

More specifically, these are the private functions and variables that are
necessary for to mimic the comparisons between datetime-like objects. Pretty
much everything was copied directly from the standard library without editing.
"""

from datetime import MAXYEAR, MINYEAR, timedelta

__all__ = [
    "_format_time",
    "_format_offset",
    "_cmp",
    "_check_int_field",
    "_days_in_month",
    "_check_datetime_fields",
    "_check_utc_offset",
    "_ymd2ord",
]

# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_DAYS_BEFORE_MONTH = [-1]  # -1 is a placeholder for indexing purposes.
dbm = 0
for dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim


def _is_leap(year):
    """year -> 1 if leap year, else 0."""
    # Copied directly from datetime
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_before_year(year):
    """year -> number of days before January 1st of year."""
    # Copied directly from datetime
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


def _days_in_month(year, month):
    """year, month -> number of days in that month in that year."""
    # Copied directly from datetime
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _days_before_month(year, month):
    """year, month -> number of days in year preceding first day of month."""
    # Copied directly from datetime
    assert 1 <= month <= 12, "month must be in 1..12"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))


def _ymd2ord(year, month, day):
    """year, month, day -> ordinal, considering 01-Jan-0001 as day 1."""
    # Copied directly from datetime
    assert 1 <= month <= 12, "month must be in 1..12"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, "day must be in 1..%d" % dim
    return _days_before_year(year) + _days_before_month(year, month) + day


def _cmp(x, y):
    # Copied directly from datetime
    return 0 if x == y else 1 if x > y else -1


def _check_utc_offset(name, offset):
    # Copied directly from datetime
    assert name in ("utcoffset", "dst")
    if offset is None:
        return
    if not isinstance(offset, timedelta):
        raise TypeError(
            "tzinfo.%s() must return None "
            "or timedelta, not '%s'" % (name, type(offset))
        )
    if not -timedelta(1) < offset < timedelta(1):
        raise ValueError(
            "%s()=%s, must be strictly between "
            "-timedelta(hours=24) and timedelta(hours=24)" % (name, offset)
        )


def _check_int_field(value):
    # Copied directly from datetime
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise TypeError("integer argument expected, got float")
    try:
        value = value.__index__()
    except AttributeError:
        pass
    else:
        if not isinstance(value, int):
            raise TypeError(
                "__index__ returned non-int (type %s)" % type(value).__name__
            )
        return value
    orig = value
    try:
        value = value.__int__()
    except AttributeError:
        pass
    else:
        if not isinstance(value, int):
            raise TypeError("__int__ returned non-int (type %s)" % type(value).__name__)
        import warnings

        warnings.warn(
            "an integer is required (got type %s)" % type(orig).__name__,
            DeprecationWarning,
            stacklevel=2,
        )
        return value
    raise TypeError("an integer is required (got type %s)" % type(value).__name__)


def _check_datetime_fields(
    year, month, day, hour, minute, second, microsecond, tzinfo, fold
):
    # Customized from version in datetime
    # Year checks
    year = _check_int_field(year)
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError("year must be in %d..%d" % (MINYEAR, MAXYEAR), year)

    # Month checks
    if month is not None:
        month = _check_int_field(month)
        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12", month)

    # Day checks
    if day is not None:
        if month is None:
            raise ValueError("Cannot specify day without month")
        day = _check_int_field(day)
        dim = _days_in_month(year, month)
        if not 1 <= day <= dim:
            raise ValueError("day must be in 1..%d" % dim, day)

    # Hour checks
    if hour is not None:
        if day is None:
            raise ValueError("Cannot specify hour without day")
        hour = _check_int_field(hour)
        if not 0 <= hour <= 23:
            raise ValueError("hour must be in 0..23", hour)

    # Minute checks
    if minute is not None:
        if hour is None:
            raise ValueError("Cannot specify minute without hour")
        minute = _check_int_field(minute)
        if not 0 <= minute <= 59:
            raise ValueError("minute must be in 0..59", minute)

    # Hour + Minute checks
    if hour is None and minute is not None:
        raise ValueError("If hour is None, minute must also be None")
    if minute is None and hour is not None:
        raise ValueError("If minute is None, hour must also be None")
    if tzinfo is not None and hour is None:
        raise ValueError("Cannot specify timezone without hour and minute")

    # Second checks
    if second is not None:
        second = _check_int_field(second)
        if not 0 <= second <= 59:
            raise ValueError("second must be in 0..59", second)

    # Microsecond, fold checks
    if microsecond is not None:
        microsecond = _check_int_field(microsecond)
        if not 0 <= microsecond <= 999999:
            raise ValueError("microsecond must be in 0..999999", microsecond)
    if fold not in (0, 1):
        raise ValueError("fold must be either 0 or 1", fold)

    return year, month, day, hour, minute, second, microsecond, tzinfo, fold


def _format_time(hh, mm, ss, us, timespec="auto"):
    # Copied directly from datetime
    specs = {
        "hours": "{:02d}",
        "minutes": "{:02d}:{:02d}",
        "seconds": "{:02d}:{:02d}:{:02d}",
        "milliseconds": "{:02d}:{:02d}:{:02d}.{:03d}",
        "microseconds": "{:02d}:{:02d}:{:02d}.{:06d}",
    }

    if timespec == "auto":
        # Skip trailing microseconds when us==0.
        timespec = "microseconds" if us else "seconds"
    elif timespec == "milliseconds":
        us //= 1000
    try:
        fmt = specs[timespec]
    except KeyError:
        raise ValueError("Unknown timespec value")
    else:
        return fmt.format(hh, mm, ss, us)


def _format_offset(off):
    # Copied directly from datetime
    s = ""
    if off is not None:
        if off.days < 0:
            sign = "-"
            off = -off
        else:
            sign = "+"
        hh, mm = divmod(off, timedelta(hours=1))
        mm, ss = divmod(mm, timedelta(minutes=1))
        s += "%s%02d:%02d" % (sign, hh, mm)
        if ss or ss.microseconds:
            s += ":%02d" % ss.seconds

            if ss.microseconds:
                s += ".%06d" % ss.microseconds
    return s

# -*- coding: utf-8 -*-
"""Functions pulled from the standard library from Python 3.9.1.

More specifically, these are the private functions and variables that are
necessary for to mimic the comparisons between datetime-like objects. Pretty
much everything was copied directly from the standard library without editing.
"""

from datetime import timedelta

__all__ = ["_format_time", "_format_offset", "_cmp"]

# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_DAYS_BEFORE_MONTH = [-1]  # -1 is a placeholder for indexing purposes.
dbm = 0
for dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim


def _cmp(x, y):
    # Copied directly from datetime
    return 0 if x == y else 1 if x > y else -1


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

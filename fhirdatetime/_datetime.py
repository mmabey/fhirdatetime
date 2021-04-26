# -*- coding: utf-8 -*-
"""Concrete date/time and related types.

See http://www.iana.org/time-zones/repository/tz-link.html for
time zone and DST data sources.
"""

import math as _math
import sys
import time as _time
from datetime import (
    date as _date_class,
    datetime as _datetime,
    time,
    time as _time_class,
    timedelta,
    timezone,
    tzinfo,
)

__all__ = [
    "_DateTime",
    "_check_int_field",
    "_check_utc_offset",
    "_cmp",
    "_days_in_month",
    "_format_offset",
    "_format_time",
    "_ymd2ord",
]


def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


_MAXORDINAL = 3652059  # date.max.toordinal()

# Utility functions, adapted from Python's Demo/classes/Dates.py, which
# also assumes the current Gregorian calendar indefinitely extended in
# both directions.  Difference:  Dates.py calls January 1 of year 0 day
# number 1.  The code here calls January 1 of year 1 day number 1.  This is
# to match the definition of the "proleptic Gregorian" calendar in Dershowitz
# and Reingold's "Calendrical Calculations", where it's the base calendar
# for all computations.  See the book for algorithms for converting between
# proleptic Gregorian ordinals and many other calendar systems.

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
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_before_year(year):
    """year -> number of days before January 1st of year."""
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


def _days_in_month(year, month):
    """year, month -> number of days in that month in that year."""
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _days_before_month(year, month):
    """year, month -> number of days in year preceding first day of month."""
    assert 1 <= month <= 12, "month must be in 1..12"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))


def _ymd2ord(year, month, day):
    """year, month, day -> ordinal, considering 01-Jan-0001 as day 1."""
    assert 1 <= month <= 12, "month must be in 1..12"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, "day must be in 1..%d" % dim
    return _days_before_year(year) + _days_before_month(year, month) + day


# Month and day names.  For localized versions, see the calendar module.
_MONTHNAMES = [
    None,
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
_DAYNAMES = [None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _build_struct_time(y, m, d, hh, mm, ss, dstflag):
    wday = (_ymd2ord(y, m, d) + 6) % 7
    dnum = _days_before_month(y, m) + d
    return _time.struct_time((y, m, d, hh, mm, ss, wday, dnum, dstflag))


def _format_time(hh, mm, ss, us, timespec="auto"):
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


# Correctly substitute for %z and %Z escapes in strftime formats.
def _wrap_strftime(object, format, timetuple):
    # Don't call utcoffset() or tzname() unless actually needed.
    freplace = None  # the string to use for %f
    zreplace = None  # the string to use for %z
    Zreplace = None  # the string to use for %Z

    # Scan format for %z and %Z escapes, replacing as needed.
    newformat = []
    push = newformat.append
    i, n = 0, len(format)
    while i < n:
        ch = format[i]
        i += 1
        if ch == "%":
            if i < n:
                ch = format[i]
                i += 1
                if ch == "f":
                    if freplace is None:
                        freplace = "%06d" % getattr(object, "microsecond", 0)
                    newformat.append(freplace)
                elif ch == "z":
                    if zreplace is None:
                        zreplace = ""
                        if hasattr(object, "utcoffset"):
                            offset = object.utcoffset()
                            if offset is not None:
                                sign = "+"
                                if offset.days < 0:
                                    offset = -offset
                                    sign = "-"
                                h, rest = divmod(offset, timedelta(hours=1))
                                m, rest = divmod(rest, timedelta(minutes=1))
                                s = rest.seconds
                                u = offset.microseconds
                                if u:
                                    zreplace = "%c%02d%02d%02d.%06d" % (
                                        sign,
                                        h,
                                        m,
                                        s,
                                        u,
                                    )
                                elif s:
                                    zreplace = "%c%02d%02d%02d" % (sign, h, m, s)
                                else:
                                    zreplace = "%c%02d%02d" % (sign, h, m)
                    assert "%" not in zreplace
                    newformat.append(zreplace)
                elif ch == "Z":
                    if Zreplace is None:
                        Zreplace = ""
                        if hasattr(object, "tzname"):
                            s = object.tzname()
                            if s is not None:
                                # strftime is going to have at this: escape %
                                Zreplace = s.replace("%", "%%")
                    newformat.append(Zreplace)
                else:
                    push("%")
                    push(ch)
            else:
                push("%")
        else:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)


# Helpers for parsing the result of isoformat()
def _parse_isoformat_date(dtstr):
    # It is assumed that this function will only be called with a
    # string of length exactly 10, and (though this is not used) ASCII-only
    year = int(dtstr[0:4])
    if dtstr[4] != "-":
        raise ValueError("Invalid date separator: %s" % dtstr[4])

    month = int(dtstr[5:7])

    if dtstr[7] != "-":
        raise ValueError("Invalid date separator")

    day = int(dtstr[8:10])

    return [year, month, day]


def _parse_hh_mm_ss_ff(tstr):
    # Parses things of the form HH[:MM[:SS[.fff[fff]]]]
    len_str = len(tstr)

    time_comps = [0, 0, 0, 0]
    pos = 0
    for comp in range(0, 3):
        if (len_str - pos) < 2:
            raise ValueError("Incomplete time component")

        time_comps[comp] = int(tstr[pos : pos + 2])

        pos += 2
        next_char = tstr[pos : pos + 1]

        if not next_char or comp >= 2:
            break

        if next_char != ":":
            raise ValueError("Invalid time separator: %c" % next_char)

        pos += 1

    if pos < len_str:
        if tstr[pos] != ".":
            raise ValueError("Invalid microsecond component")
        else:
            pos += 1

            len_remainder = len_str - pos
            if len_remainder not in (3, 6):
                raise ValueError("Invalid microsecond component")

            time_comps[3] = int(tstr[pos:])
            if len_remainder == 3:
                time_comps[3] *= 1000

    return time_comps


def _parse_isoformat_time(tstr):
    # Format supported is HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]
    len_str = len(tstr)
    if len_str < 2:
        raise ValueError("Isoformat time too short")

    # This is equivalent to re.search('[+-]', tstr), but faster
    tz_pos = tstr.find("-") + 1 or tstr.find("+") + 1
    timestr = tstr[: tz_pos - 1] if tz_pos > 0 else tstr

    time_comps = _parse_hh_mm_ss_ff(timestr)

    tzi = None
    if tz_pos > 0:
        tzstr = tstr[tz_pos:]

        # Valid time zone strings are:
        # HH:MM               len: 5
        # HH:MM:SS            len: 8
        # HH:MM:SS.ffffff     len: 15

        if len(tzstr) not in (5, 8, 15):
            raise ValueError("Malformed time zone string")

        tz_comps = _parse_hh_mm_ss_ff(tzstr)
        if all(x == 0 for x in tz_comps):
            tzi = timezone.utc
        else:
            tzsign = -1 if tstr[tz_pos - 1] == "-" else 1

            td = timedelta(
                hours=tz_comps[0],
                minutes=tz_comps[1],
                seconds=tz_comps[2],
                microseconds=tz_comps[3],
            )

            tzi = timezone(tzsign * td)

    time_comps.append(tzi)

    return time_comps


# Just raise TypeError if the arg isn't None or a string.
def _check_tzname(name):
    if name is not None and not isinstance(name, str):
        raise TypeError(
            "tzinfo.tzname() must return None or string, " "not '%s'" % type(name)
        )


# name is the offset-producing method, "utcoffset" or "dst".
# offset is what it returned.
# If offset isn't None or timedelta, raises TypeError.
# If offset is None, returns None.
# Else offset is checked for being in range.
# If it is, its integer value is returned.  Else ValueError is raised.
def _check_utc_offset(name, offset):
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


def _check_tzinfo_arg(tz):
    if tz is not None and not isinstance(tz, tzinfo):
        raise TypeError("tzinfo argument must be None or of a tzinfo subclass")


def _cmperror(x, y):
    raise TypeError("can't compare '%s' to '%s'" % (type(x).__name__, type(y).__name__))


class IsoCalendarDate(tuple):
    def __new__(cls, year, week, weekday):
        return super().__new__(cls, (year, week, weekday))

    @property
    def year(self):
        return self[0]

    @property
    def week(self):
        return self[1]

    @property
    def weekday(self):
        return self[2]

    def __reduce__(self):
        # This code is intended to pickle the object without making the
        # class public. See https://bugs.python.org/msg352381
        return (tuple, (tuple(self),))

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"(year={self[0]}, week={self[1]}, weekday={self[2]})"
        )


_IsoCalendarDate = IsoCalendarDate
del IsoCalendarDate
_tzinfo_class = tzinfo


class _DateTime:
    """datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])

    The year, month and day arguments are required. tzinfo may be None, or an
    instance of a tzinfo subclass. The remaining arguments may be ints.
    """

    # def __new__(cls, *_, **__):
    #     # Customized to circumvent the tangled web that is datetime.__new__()
    #     return _datetime.__new__(cls, 1, 1, 1)

    def __init__(
        self,
        year,
        month=None,
        day=None,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        *,
        fold=0,
    ):
        # Only stores the values given (does no validation of values)
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._hashcode = -1
        self._fold = fold

    # Read-only field accessors
    @property
    def year(self):
        """year (1-9999)"""
        return self._year

    @property
    def month(self):
        """month (1-12)"""
        return self._month

    @property
    def day(self):
        """day (1-31)"""
        return self._day

    @property
    def hour(self):
        """hour (0-23)"""
        return self._hour

    @property
    def minute(self):
        """minute (0-59)"""
        return self._minute

    @property
    def second(self):
        """second (0-59)"""
        return self._second

    @property
    def microsecond(self):
        """microsecond (0-999999)"""
        return self._microsecond

    @property
    def tzinfo(self):
        """timezone info object"""
        return self._tzinfo

    @property
    def fold(self):
        return self._fold

    @classmethod
    def _fromtimestamp(cls, t, utc, tz):
        """Construct a datetime from a POSIX timestamp (like time.time()).

        A timezone info object may be passed in as well.
        """
        frac, t = _math.modf(t)
        us = round(frac * 1e6)
        if us >= 1000000:
            t += 1
            us -= 1000000
        elif us < 0:
            t -= 1
            us += 1000000

        converter = _time.gmtime if utc else _time.localtime
        y, m, d, hh, mm, ss, weekday, jday, dst = converter(t)
        ss = min(ss, 59)  # clamp out leap seconds if the platform has them
        result = cls(y, m, d, hh, mm, ss, us, tz)
        if tz is None:
            # As of version 2015f max fold in IANA database is
            # 23 hours at 1969-09-30 13:00:00 in Kwajalein.
            # Let's probe 24 hours in the past to detect a transition:
            max_fold_seconds = 24 * 3600

            # On Windows localtime_s throws an OSError for negative values,
            # thus we can't perform fold detection for values of time less
            # than the max time fold. See comments in _datetimemodule's
            # version of this method for more details.
            if t < max_fold_seconds and sys.platform.startswith("win"):
                return result

            y, m, d, hh, mm, ss = converter(t - max_fold_seconds)[:6]
            probe1 = cls(y, m, d, hh, mm, ss, us, tz)
            trans = result - probe1 - timedelta(0, max_fold_seconds)
            if trans.days < 0:
                y, m, d, hh, mm, ss = converter(t + trans // timedelta(0, 1))[:6]
                probe2 = cls(y, m, d, hh, mm, ss, us, tz)
                if probe2 == result:
                    result._fold = 1
        else:
            result = tz.fromutc(result)
        return result

    @classmethod
    def fromtimestamp(cls, t, tz=None):
        """Construct a datetime from a POSIX timestamp (like time.time()).

        A timezone info object may be passed in as well.
        """
        _check_tzinfo_arg(tz)

        return cls._fromtimestamp(t, tz is not None, tz)

    @classmethod
    def utcfromtimestamp(cls, t):
        """Construct a naive UTC datetime from a POSIX timestamp."""
        return cls._fromtimestamp(t, True, None)

    @classmethod
    def now(cls, tz=None):
        "Construct a datetime from time.time() and optional time zone info."
        t = _time.time()
        return cls.fromtimestamp(t, tz)

    @classmethod
    def utcnow(cls):
        "Construct a UTC datetime from time.time()."
        t = _time.time()
        return cls.utcfromtimestamp(t)

    @classmethod
    def combine(cls, date, time, tzinfo=True):
        "Construct a datetime from a given date and a given time."
        if not isinstance(date, _date_class):
            raise TypeError("date argument must be a date instance")
        if not isinstance(time, _time_class):
            raise TypeError("time argument must be a time instance")
        if tzinfo is True:
            tzinfo = time.tzinfo
        return cls(
            date.year,
            date.month,
            date.day,
            time.hour,
            time.minute,
            time.second,
            time.microsecond,
            tzinfo,
            fold=time.fold,
        )

    @classmethod
    def fromisoformat(cls, date_string):
        """Construct a datetime from the output of datetime.isoformat()."""
        if not isinstance(date_string, str):
            raise TypeError("fromisoformat: argument must be str")

        # Split this at the separator
        dstr = date_string[0:10]
        tstr = date_string[11:]

        try:
            date_components = _parse_isoformat_date(dstr)
        except ValueError:
            raise ValueError(f"Invalid isoformat string: {date_string!r}")

        if tstr:
            try:
                time_components = _parse_isoformat_time(tstr)
            except ValueError:
                raise ValueError(f"Invalid isoformat string: {date_string!r}")
        else:
            time_components = [0, 0, 0, 0, None]

        return cls(*(date_components + time_components))

    def timetuple(self):
        """Return local time tuple compatible with time.localtime()."""
        dst = self.dst()
        if dst is None:
            dst = -1
        elif dst:
            dst = 1
        else:
            dst = 0
        return _build_struct_time(
            self.year, self.month, self.day, self.hour, self.minute, self.second, dst
        )

    def _mktime(self):
        """Return integer POSIX timestamp."""
        epoch = _DateTime(1970, 1, 1)
        max_fold_seconds = 24 * 3600
        t = (self - epoch) // timedelta(0, 1)

        def local(u):
            y, m, d, hh, mm, ss = _time.localtime(u)[:6]
            return (_DateTime(y, m, d, hh, mm, ss) - epoch) // timedelta(0, 1)

        # Our goal is to solve t = local(u) for u.
        a = local(t) - t
        u1 = t - a
        t1 = local(u1)
        if t1 == t:
            # We found one solution, but it may not be the one we need.
            # Look for an earlier solution (if `fold` is 0), or a
            # later one (if `fold` is 1).
            u2 = u1 + (-max_fold_seconds, max_fold_seconds)[self.fold]
            b = local(u2) - u2
            if a == b:
                return u1
        else:
            b = t1 - u1
            assert a != b
        u2 = t - b
        t2 = local(u2)
        if t2 == t:
            return u2
        if t1 == t:
            return u1
        # We have found both offsets a and b, but neither t - a nor t - b is
        # a solution.  This means t is in the gap.
        return (max, min)[self.fold](u1, u2)

    def timestamp(self):
        "Return POSIX timestamp as float"
        if self._tzinfo is None:
            s = self._mktime()
            return s + self.microsecond / 1e6
        else:
            return (self - _EPOCH).total_seconds()

    def utctimetuple(self):
        "Return UTC time tuple compatible with time.gmtime()."
        offset = self.utcoffset()
        if offset:
            self -= offset
        y, m, d = self.year, self.month, self.day
        hh, mm, ss = self.hour, self.minute, self.second
        return _build_struct_time(y, m, d, hh, mm, ss, 0)

    def date(self):
        "Return the date part."
        return _date_class(self._year, self._month, self._day)

    def time(self):
        "Return the time part, with tzinfo None."
        return time(
            self.hour, self.minute, self.second, self.microsecond, fold=self.fold
        )

    def timetz(self):
        "Return the time part, with same tzinfo."
        return time(
            self.hour,
            self.minute,
            self.second,
            self.microsecond,
            self._tzinfo,
            fold=self.fold,
        )

    def replace(
        self,
        year=None,
        month=None,
        day=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        tzinfo=True,
        *,
        fold=None,
    ):
        """Return a new datetime with new values for the specified fields."""
        if year is None:
            year = self.year
        if month is None:
            month = self.month
        if day is None:
            day = self.day
        if hour is None:
            hour = self.hour
        if minute is None:
            minute = self.minute
        if second is None:
            second = self.second
        if microsecond is None:
            microsecond = self.microsecond
        if tzinfo is True:
            tzinfo = self.tzinfo
        if fold is None:
            fold = self.fold
        return type(self)(
            year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )

    def _local_timezone(self):
        if self.tzinfo is None:
            ts = self._mktime()
        else:
            ts = (self - _EPOCH) // timedelta(seconds=1)
        localtm = _time.localtime(ts)
        local = _DateTime(*localtm[:6])
        # Extract TZ data
        gmtoff = localtm.tm_gmtoff
        zone = localtm.tm_zone
        return timezone(timedelta(seconds=gmtoff), zone)

    def astimezone(self, tz=None):
        if tz is None:
            tz = self._local_timezone()
        elif not isinstance(tz, tzinfo):
            raise TypeError("tz argument must be an instance of tzinfo")

        mytz = self.tzinfo
        if mytz is None:
            mytz = self._local_timezone()
            myoffset = mytz.utcoffset(self)
        else:
            myoffset = mytz.utcoffset(self)
            if myoffset is None:
                mytz = self.replace(tzinfo=None)._local_timezone()
                myoffset = mytz.utcoffset(self)

        if tz is mytz:
            return self

        # Convert self to UTC, and attach the new time zone object.
        utc = (self - myoffset).replace(tzinfo=tz)

        # Convert from UTC to tz's local time.
        return tz.fromutc(utc)

    # Ways to produce a string.

    def ctime(self):
        "Return ctime() style string."
        weekday = self.toordinal() % 7 or 7
        return "%s %s %2d %02d:%02d:%02d %04d" % (
            _DAYNAMES[weekday],
            _MONTHNAMES[self._month],
            self._day,
            self._hour,
            self._minute,
            self._second,
            self._year,
        )

    def isoformat(self, sep="T", timespec="auto"):
        """Return the time formatted according to ISO.

        The full format looks like 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
        By default, the fractional part is omitted if self.microsecond == 0.

        If self.tzinfo is not None, the UTC offset is also attached, giving
        giving a full format of 'YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM'.

        Optional argument sep specifies the separator between date and
        time, default 'T'.

        The optional argument timespec specifies the number of additional
        terms of the time to include. Valid options are 'auto', 'hours',
        'minutes', 'seconds', 'milliseconds' and 'microseconds'.
        """
        s = "%04d-%02d-%02d%c" % (
            self._year,
            self._month,
            self._day,
            sep,
        ) + _format_time(
            self._hour, self._minute, self._second, self._microsecond, timespec
        )

        off = self.utcoffset()
        tz = _format_offset(off)
        if tz:
            s += tz

        return s

    def __repr__(self):
        """Convert to formal string, for repr()."""
        L = [
            self._year,
            self._month,
            self._day,  # These are never zero
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
        ]
        if L[-1] == 0:
            del L[-1]
        if L[-1] == 0:
            del L[-1]
        s = "%s.%s(%s)" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            ", ".join(map(str, L)),
        )
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        if self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def __str__(self):
        """Convert to string, for str()."""
        return self.isoformat(sep=" ")

    def strftime(self, fmt):
        """Format using strftime()."""
        return _wrap_strftime(self, fmt, self.timetuple())

    def __format__(self, fmt):
        if not isinstance(fmt, str):
            raise TypeError("must be str, not %s" % type(fmt).__name__)
        if len(fmt) != 0:
            return self.strftime(fmt)
        return str(self)

    @classmethod
    def strptime(cls, date_string, format):
        "string, format -> new datetime parsed from a string (like time.strptime())."
        import _strptime

        return _strptime._strptime_datetime(cls, date_string, format)

    def utcoffset(self):
        """Return the timezone offset as timedelta positive east of UTC (negative west of
        UTC)."""
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(self)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        if self._tzinfo is None:
            return None
        name = self._tzinfo.tzname(self)
        _check_tzname(name)
        return name

    def dst(self):
        """Return 0 if DST is not in effect, or the DST offset (as timedelta
        positive eastward) if DST is in effect.

        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() if applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST
        info.
        """
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.dst(self)
        _check_utc_offset("dst", offset)
        return offset

    # Standard conversions, __eq__, __le__, __lt__, __ge__, __gt__,
    # __hash__ (and helpers)

    def toordinal(self):
        """Return proleptic Gregorian ordinal for the year, month and day.

        January 1 of year 1 is day 1.  Only the year, month and day values
        contribute to the result.
        """
        return _ymd2ord(self._year, self._month, self._day)

    # Comparisons of datetime objects with other.

    def __eq__(self, other):
        if isinstance(other, (_DateTime, _datetime)):
            return self._cmp(other, allow_mixed=True) == 0
        elif not isinstance(other, _date_class):
            return NotImplemented
        else:
            return False

    def __le__(self, other):
        if isinstance(other, (_DateTime, _datetime)):
            return self._cmp(other) <= 0
        elif not isinstance(other, _date_class):
            return NotImplemented
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, (_DateTime, _datetime)):
            return self._cmp(other) < 0
        elif not isinstance(other, _date_class):
            return NotImplemented
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, (_DateTime, _datetime)):
            return self._cmp(other) >= 0
        elif not isinstance(other, _date_class):
            return NotImplemented
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, (_DateTime, _datetime)):
            return self._cmp(other) > 0
        elif not isinstance(other, _date_class):
            return NotImplemented
        else:
            _cmperror(self, other)

    def _cmp(self, other, allow_mixed=False):
        assert isinstance(other, (_DateTime, _datetime))
        mytz = self._tzinfo
        ottz = other._tzinfo
        myoff = otoff = None

        if mytz is ottz:
            base_compare = True
        else:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            # Assume that allow_mixed means that we are called from __eq__
            if allow_mixed:
                if myoff != self.replace(fold=not self.fold).utcoffset():
                    return 2
                if otoff != other.replace(fold=not other.fold).utcoffset():
                    return 2
            base_compare = myoff == otoff

        if base_compare:
            return _cmp(
                (
                    self._year,
                    self._month,
                    self._day,
                    self._hour,
                    self._minute,
                    self._second,
                    self._microsecond,
                ),
                (
                    other._year,
                    other._month,
                    other._day,
                    other._hour,
                    other._minute,
                    other._second,
                    other._microsecond,
                ),
            )
        if myoff is None or otoff is None:
            if allow_mixed:
                return 2  # arbitrary non-zero value
            else:
                raise TypeError("cannot compare naive and aware datetimes")
        # XXX What follows could be done more efficiently...
        diff = self - other  # this will take offsets into account
        if diff.days < 0:
            return -1
        return diff and 1 or 0

    # Computations

    def __add__(self, other):
        """Add a datetime and a timedelta."""
        if not isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(
            self.toordinal(),
            hours=self._hour,
            minutes=self._minute,
            seconds=self._second,
            microseconds=self._microsecond,
        )
        delta += other
        hour, rem = divmod(delta.seconds, 3600)
        minute, second = divmod(rem, 60)
        if 0 < delta.days <= _MAXORDINAL:
            return type(self).combine(
                _date_class.fromordinal(delta.days),
                time(hour, minute, second, delta.microseconds, tzinfo=self._tzinfo),
            )
        raise OverflowError("result out of range")

    __radd__ = __add__

    def __sub__(self, other):
        """Subtract two datetimes, or a datetime and a timedelta."""
        if not isinstance(other, (_DateTime, _datetime)):
            if isinstance(other, timedelta):
                return self + -other
            return NotImplemented

        days1 = self.toordinal()
        days2 = other.toordinal()
        secs1 = self._second + self._minute * 60 + self._hour * 3600
        secs2 = other.second + other.minute * 60 + other.hour * 3600
        base = timedelta(
            days1 - days2, secs1 - secs2, self._microsecond - other.microsecond
        )
        if self._tzinfo is other.tzinfo:
            return base
        myoff = self.utcoffset()
        otoff = other.utcoffset()
        if myoff == otoff:
            return base
        if myoff is None or otoff is None:
            raise TypeError("cannot mix naive and timezone-aware time")
        return base + otoff - myoff

    def __hash__(self):
        if self._hashcode == -1:
            if self.fold:
                t = self.replace(fold=0)
            else:
                t = self
            tzoff = t.utcoffset()
            if tzoff is None:
                self._hashcode = hash(t._getstate()[0])
            else:
                days = _ymd2ord(self.year, self.month, self.day)
                seconds = self.hour * 3600 + self.minute * 60 + self.second
                self._hashcode = hash(
                    timedelta(days, seconds, self.microsecond) - tzoff
                )
        return self._hashcode

    # Day-of-the-week and week-of-the-year, according to ISO

    def weekday(self):
        """Return day of the week, where Monday == 0 ... Sunday == 6."""
        return (self.toordinal() + 6) % 7

    def isoweekday(self):
        """Return day of the week, where Monday == 1 ... Sunday == 7."""
        # 1-Jan-0001 is a Monday
        return self.toordinal() % 7 or 7

    def isocalendar(self):
        """Return a named tuple containing ISO year, week number, and weekday.

        The first ISO week of the year is the (Mon-Sun) week
        containing the year's first Thursday; everything else derives
        from that.

        The first week is 1; Monday is 1 ... Sunday is 7.

        ISO calendar algorithm taken from
        http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        (used with permission)
        """
        year = self._year
        week1monday = _isoweek1monday(year)
        today = _ymd2ord(self._year, self._month, self._day)
        # Internally, week and day have origin 0
        week, day = divmod(today - week1monday, 7)
        if week < 0:
            year -= 1
            week1monday = _isoweek1monday(year)
            week, day = divmod(today - week1monday, 7)
        elif week >= 52:
            if today >= _isoweek1monday(year + 1):
                year += 1
                week = 0
        return _IsoCalendarDate(year, week + 1, day + 1)

    # Pickle support.

    def _getstate(self, protocol=3):
        yhi, ylo = divmod(self._year, 256)
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        m = self._month
        if self._fold and protocol > 3:
            m += 128
        basestate = bytes(
            [
                yhi,
                ylo,
                m,
                self._day,
                self._hour,
                self._minute,
                self._second,
                us1,
                us2,
                us3,
            ]
        )
        if self._tzinfo is None:
            return (basestate,)
        else:
            return (basestate, self._tzinfo)

    def __setstate(self, string, tzinfo):
        if tzinfo is not None and not isinstance(tzinfo, _tzinfo_class):
            raise TypeError("bad tzinfo state arg")
        (
            yhi,
            ylo,
            m,
            self._day,
            self._hour,
            self._minute,
            self._second,
            us1,
            us2,
            us3,
        ) = string
        if m > 127:
            self._fold = 1
            self._month = m - 128
        else:
            self._fold = 0
            self._month = m
        self._year = yhi * 256 + ylo
        self._microsecond = (((us1 << 8) | us2) << 8) | us3
        self._tzinfo = tzinfo

    def __reduce_ex__(self, protocol):
        return self.__class__, self._getstate(protocol)

    def __reduce__(self):
        return self.__reduce_ex__(2)


_DateTime.min = _DateTime(1, 1, 1)
_DateTime.max = _DateTime(9999, 12, 31, 23, 59, 59, 999999)
_DateTime.resolution = timedelta(microseconds=1)


def _isoweek1monday(year):
    # Helper to calculate the day number of the Monday starting week 1
    # XXX This could be done more efficiently
    THURSDAY = 3
    firstday = _ymd2ord(year, 1, 1)
    firstweekday = (firstday + 6) % 7  # See weekday() above
    week1monday = firstday - firstweekday
    if firstweekday > THURSDAY:
        week1monday += 7
    return week1monday


_EPOCH = _DateTime(1970, 1, 1, tzinfo=timezone.utc)

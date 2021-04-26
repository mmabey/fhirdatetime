# -*- coding: utf-8 -*-
"""A datetime-compatible class for FHIR date/datetime values.

The `FHIR specification <https://www.hl7.org/fhir/>`_ from HL7 is "a
standard for health care data exchange." The FHIR spec includes
`date <https://www.hl7.org/fhir/datatypes.html#date>`_ and
`datetime <https://www.hl7.org/fhir/datatypes.html#dateTime>`_ data types
that provide more flexibility than the standard Python :class:`date` and
:class:`datetime` types. This makes sense when you consider a patient may
report to their provider that they have experience a particular symptom
since a particular year without knowing the month or day of onset.

The purpose of this class is to allow for this flexibility without
sacrificing the ability to compare (using <, >, ==, etc.) against objects
of the same type as well as :class:`date` and :class:`datetime` objects.

When comparing objects, only the values that are populated for *both*
objects are considered. Consider the following examples in which only the
years are compared:

>>> FhirDateTime(2021) == FhirDateTime(2021, 3, 15)
True
>>> FhirDateTime(2021) == datetime(2021, 3, 15, 23, 56)
True
>>> FhirDateTime(2021) == date(2021, 3, 15)
True
>>> FhirDateTime(2021) < FhirDateTime(2021, 3, 15)
False
>>> FhirDateTime(2021) > FhirDateTime(2021, 3, 15)
False
"""
from datetime import MAXYEAR, MINYEAR, date, datetime, timezone, tzinfo as tzinfo_
from operator import itemgetter
from typing import Optional, Union

from ._datetime import (
    _check_int_field,
    _cmp,
    _DateTime,
    _days_in_month,
    _format_offset,
    _format_time,
)

__all__ = ["FhirDateTime", "__version__"]
__version__ = "0.1.0b5"

DATE_FIELDS = ("year", "month", "day")
TIME_FIELDS = ("hour", "minute", "second", "microsecond")

ComparableTypes = Union["FhirDateTime", datetime, date]


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


class FhirDateTime(_DateTime, datetime):
    """Type for representing datetime values from FHIR data."""

    def __new__(cls, year, *_, **__) -> "FhirDateTime":
        """Start creating FhirDateTime instance."""
        # Give datetime.__new__() an arbitrary date to pass its value checks
        return super().__new__(cls, 1, 1, 1)

    def __init__(
        self,
        year: Union[int, str, datetime, date],
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Optional[tzinfo_] = None,
        *,
        fold: int = 0,
    ):
        """Create new FhirDateTime instance.

        :param year: Only required value [1, 9999].
        :param month: Optional [1-12].
        :param day: Optional [1-31].
        :param hour: Optional [0-23].
        :param minute: Optional [0-59].
        :param second: Optional [0-59].
        :param microsecond: Optional [0-999999].
        :param tzinfo: Optional timezone instance.
        :param fold: In [0, 1]. See standard lib docs for more info.
        :returns: New instance of FhirDateTime.
        """
        if isinstance(year, (datetime, date)):
            self._replace_with(year)
            return
        if isinstance(year, str):
            dt = FhirDateTime.fromisoformat(year)
            self._replace_with(dt)
            return

        # Check values are within acceptable ranges
        (
            year,
            month,
            day,
            hour,
            minute,
            second,
            microsecond,
            tzinfo,
            fold,
        ) = _check_datetime_fields(
            year, month, day, hour, minute, second, microsecond, tzinfo, fold
        )
        super().__init__(
            year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )

    def isoformat(self, sep: str = "T", timespec: str = "auto") -> str:
        """Return the time formatted according to ISO.

        The full format looks like 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
        By default, any missing part is omitted.

        If self.tzinfo is not None, the UTC offset is also attached, giving
        giving a full format of 'YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM'.

        Optional argument sep specifies the separator between date and
        time, default 'T'.

        The optional argument timespec specifies the number of additional
        terms of the time to include. Valid options are 'auto', 'hours',
        'minutes', 'seconds', 'milliseconds' and 'microseconds'.
        """
        y = "{_year:04d}"
        ym = y + "-{_month:02d}"
        ymd = ym + "-{_day:02d}"
        ymdt = ymd + f"{sep}" + "{t}"
        t = ""

        if self._month is None:
            fmt = y
        elif self._day is None:
            fmt = ym
        elif None in {self._hour, self._minute}:
            fmt = ymd
        else:
            fmt = ymdt
            t = _format_time(
                self._hour, self._minute, self._second, self._microsecond, timespec
            )

        s = fmt.format(**{"t": t, **self.__dict__})
        off = self.utcoffset()
        tz = _format_offset(off)
        if tz:
            s += tz

        return s

    @classmethod
    def fromisoformat(cls, date_string: str):
        """Construct a FhirDateTime from the output of FhirDateTime.isoformat()."""
        try:
            return super().fromisoformat(date_string)
        except (ValueError, IndexError):
            pass

        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%Z", "%Y", "%Y-%m", "%Y-%m-%d"):
            try:
                return cls.strptime(date_string, fmt)
            except ValueError as err:
                last_err = err
                continue
        try:
            return cls.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            pass
        raise last_err

    @staticmethod
    def from_native(other: Union[datetime, date]) -> "FhirDateTime":
        """Create instance from standard lib date or datetime obj."""
        dt = FhirDateTime(1)  # Just an arbitrary year
        dt._replace_with(other)
        return dt

    def _replace_with(self, other):
        if not isinstance(other, (FhirDateTime, date, datetime)):
            raise TypeError(
                f"Can only create FhirDateTime from date, datetime types, "
                f"got {type(other).__name__}"
            )
        self._year = other.year
        self._month = other.month
        self._day = other.day
        if isinstance(other, (FhirDateTime, datetime)):
            self._hour = other.hour
            self._minute = other.minute
            self._second = other.second
            self._microsecond = other.microsecond
            self._tzinfo = other.tzinfo
            self._fold = other.fold
        else:
            self._hour = None
            self._minute = None
            self._second = None
            self._microsecond = None
            self._tzinfo = None
            self._fold = 0

    @staticmethod
    def sort_key(attr_path: Optional[str] = None):
        """Create a function appropriate for use as a sorting key.

        .. important:: When there is ambiguity due to one :class:`FhirDateTime`
            object storing less-granular data than another (e.g.,
            ``FhirDateTime(2021)`` vs. ``FhirDateTime(2021, 4)``), objects with
            missing values will be ordered *before* those with more granular
            values that would otherwise be considered equivalent when using the
            ``==`` operator.

        When you need to sort a sequence of either :class:`FhirDateTime`
        objects or object that *contain* a :class:`FhirDateTime` object, this
        function will make it easier to sort the items properly.

        There are two ways to use this function. The first is intended for use
        when sorting a sequence of  :class:`FhirDateTime` objects, something
        like this (notice that ``sort_key()`` is called with no parameters):

        >>> sorted(
        ...     [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
        ...     key=FhirDateTime.sort_key()
        ... )
        [FhirDateTime(2021), FhirDateTime(2021, 4), FhirDateTime(2021, 4, 12)]

        The second is for use when sorting a sequence of objects that have
        :class:`FhirDateTime` objects as attributes. This example sorts the
        ``CarePlan`` objects by the care plan's period's start date:

        >>> care_plan_list = [...]
        >>> sorted(care_plan_list, key=FhirDateTime.sort_key("period.start"))

        In this example, ``sorted()`` passes each item in ``care_plan_list`` to
        the ``sort_key`` static method, which first gets the ``period``
        attribute of the item, then gets the ``start`` attribute of the period.
        Finally, the year, month, day, and other values are returned to
        ``sorted()``, which does the appropriate sorting on those values.

        :param attr_path: A attribute "path" to the :class:`FhirDateTime`
            object to be used as the basis for sorting, such as
            ``"period.start"``.
        :return: A function identifying values to use for sorting.
        """
        i = itemgetter(0, 1, 2, 3, 4, 5, 6)
        if attr_path is None:
            return i

        def caller(obj):
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
            if not isinstance(obj, FhirDateTime):
                raise TypeError(
                    f"attr_path must lead to an instance of FhirDateTime, "
                    f"not {type(obj).__name__}"
                )
            return i(obj)

        return caller

    def _cmp(self, other: ComparableTypes, *_):
        if not isinstance(other, (FhirDateTime, datetime, date)):
            raise TypeError(f"Cannot compare FhirDateTime and {type(other).__name__}")

        mytz = self.tzinfo
        ottz = getattr(other, "tzinfo", None)

        if mytz is ottz or None in {mytz, ottz}:
            base_compare = True
        else:
            myoff = self.utcoffset()
            # other must have a utcoffset value here because ottz must be non-None
            otoff = other.utcoffset()
            base_compare = myoff == otoff

        if base_compare:
            for f in DATE_FIELDS + TIME_FIELDS:
                my = getattr(self, f, None)
                ot = getattr(other, f, None)
                if None in {my, ot}:
                    return 0
                c = _cmp(my, ot)
                if c != 0:
                    return c
            # Means all fields are the same and non-None
            return 0

        # If we've reached this point, self has time values and other must be a
        # FhirDateTime or datetime object.
        diff = self - other
        if diff.days < 0:
            return -1
        return diff and 1 or 0

    def __eq__(self, other: ComparableTypes):
        return self._cmp(other) == 0

    def __ne__(self, other: ComparableTypes):
        return self._cmp(other) != 0

    def __le__(self, other: ComparableTypes):
        return self._cmp(other) <= 0

    def __lt__(self, other: ComparableTypes):
        return self._cmp(other) < 0

    def __ge__(self, other: ComparableTypes):
        return self._cmp(other) >= 0

    def __gt__(self, other: ComparableTypes):
        return self._cmp(other) > 0

    def __repr__(self):
        """Convert to formal string, for repr()."""
        f = [
            self._year,
            self._month,
            self._day,
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
        ]
        while f[-1] in {0, None}:
            del f[-1]
        s = "%s.%s(%s)" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            ", ".join(map(str, f)),
        )
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        if self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    def __getitem__(self, item):
        if item == 0:
            val = self.year
        elif item == 1:
            val = self.month
        elif item == 2:
            val = self.day
        elif item == 3:
            val = self.hour
        elif item == 4:
            val = self.minute
        elif item == 5:
            val = self.second
        elif item == 6:
            val = self.microsecond
        else:
            raise IndexError("Valid indexes are 0-6")

        if val is None:
            # Assume we're accessing for sorting purposes and empty values come first
            val = -1
        return val

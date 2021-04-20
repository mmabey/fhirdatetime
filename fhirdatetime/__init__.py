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

>>> DateTime(2021) == DateTime(2021, 3, 15)
True
>>> DateTime(2021) == datetime(2021, 3, 15, 23, 56)
True
>>> DateTime(2021) == date(2021, 3, 15)
True
>>> DateTime(2021) < DateTime(2021, 3, 15)
False
>>> DateTime(2021) > DateTime(2021, 3, 15)
False
"""

from datetime import date, datetime
from datetime import tzinfo as tzinfo_
from operator import itemgetter
from typing import Optional, Union

from ._datetime import _cmp, _format_offset, _format_time

__all__ = ["DateTime", "__version__"]
__version__ = "0.1.0b1"

DATE_FIELDS = ("year", "month", "day")
TIME_FIELDS = ("hour", "minute", "second", "microsecond")

ComparableTypes = Union["DateTime", datetime, date]


class DateTime(datetime):
    """Type for representing datetime values from FHIR data."""

    def __new__(
        cls,
        year: int,
        month: Optional[int] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Optional[tzinfo_] = None,
        *,
        fold: int = 0,
    ) -> "DateTime":
        """Create new instance.

        :param year: Only required value [1, 9999].
        :param month: Optional [1-12].
        :param day: Optional [1-31].
        :param hour: Optional [0-23].
        :param minute: Optional [0-59].
        :param second: Optional [0-59].
        :param microsecond: Optional [0-999999].
        :param tzinfo: Optional timezone instance.
        :param fold: In [0, 1]. See standard lib docs for more info.
        :returns: New instance of DateTime.
        :raises ValueError: When an invalid value for a field is provided.
        """
        if isinstance(year, (datetime, date)):
            return DateTime.from_native(year)
        if isinstance(year, str):
            return DateTime.fromisoformat(year)

        # To create an instance, we have to call datetime.__new__, but getting that to
        # not raise errors requires passing it values that conform to datetime's
        # requirements (such as having at least a year, month, and day). So, we save the
        # values originally passed to this __new__() to store after calling datetime's
        # __new__(). At the same time, we also check that more granular values aren't
        # provided if less granular values aren't also provided (can't give a day
        # without a month).
        orig_month = month
        orig_day = day
        orig_hour = hour
        orig_minute = minute

        if month is None:
            month = 1

        if day is None:
            day = 1
        elif orig_month is None:
            raise ValueError("Cannot specify day without month")

        if hour is None:
            if orig_minute is not None:
                raise ValueError("If hour is None, minute must also be None")
            hour = 0
        elif orig_day is None:
            raise ValueError("Cannot specify hour without day")

        if minute is None:
            if orig_hour is not None:
                raise ValueError("If minute is None, hour must also be None")
            minute = 0
        elif orig_hour is None:
            raise ValueError("Cannot specify minute without hour")

        if tzinfo is not None:
            if orig_hour is None:
                raise ValueError("Cannot specify timezone without hour and minute")

        self = super().__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )
        # Not sure why, but none of these values are set after calling super().__new__()
        self._year = year
        self._month = orig_month
        self._day = orig_day
        self._hour = orig_hour
        self._minute = orig_minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._hashcode = -1
        self._fold = fold
        return self

    # Read-only field accessors - The datetime versions of these don't work 🤷
    @property
    def year(self):
        """Year (1-9999)."""
        return self._year

    @property
    def month(self):
        """Month (1-12)."""
        return self._month

    @property
    def day(self):
        """Day (1-31)."""
        return self._day

    @property
    def hour(self):
        """Hour (0-23)."""
        return self._hour

    @property
    def minute(self):
        """Minute (0-59)."""
        return self._minute

    @property
    def second(self):
        """Second (0-59)."""
        return self._second

    @property
    def microsecond(self):
        """Microsecond (0-999999)."""
        return self._microsecond

    @property
    def tzinfo(self):
        """Timezone info object."""
        return self._tzinfo

    @property
    def fold(self):
        """Fold value."""
        return self._fold

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
        """Construct a DateTime from the output of DateTime.isoformat()."""
        try:
            return super().fromisoformat(date_string)
        except ValueError:
            pass

        for fmt in ("%Y", "%Y-%m", "%Y-%m-%d"):
            try:
                return cls.strptime(date_string, fmt)
            except ValueError as err:
                last_err = err
                continue
        raise last_err

    @staticmethod
    def from_native(other: Union[datetime, date]):
        """Create instance from standard lib date or datetime obj."""
        if isinstance(other, datetime):
            return DateTime(
                other.year,
                other.month,
                other.day,
                other.hour,
                other.minute,
                other.second,
                other.microsecond,
                other.tzinfo,
                fold=other.fold,
            )
        elif isinstance(other, date):
            return DateTime(other.year, other.month, other.day)
        raise TypeError(
            f"Can only create DateTime from date and datetime types, got {type(other)}"
        )

    @staticmethod
    def sort_key(attr_path: Optional[str] = None):
        """Create a function appropriate for use as a sorting key.

        .. important:: When there is ambiguity due to one :class:`DateTime` object
            storing less-granular data than another (e.g., ``DateTime(2021)``
            vs. ``DateTime(2021, 4)``), objects with missing values will be
            ordered *before* those with more granular values that would
            otherwise be considered equivalent when using the ``==`` operator.

        When you need to sort a sequence of either :class:`DateTime` objects or
        object that *contain* a :class:`DateTime` object, this function will
        make it easier to sort the items properly.

        There are two ways to use this function. The first is intended for use
        when sorting a sequence of  :class:`DateTime` objects, something like
        this (notice that ``sort_key()`` is called with no parameters):

        >>> sorted(
        ...     [DateTime(2021, 4), DateTime(2021), DateTime(2021, 4, 12)],
        ...     key=DateTime.sort_key()
        ... )
        [DateTime(2021), DateTime(2021, 4), DateTime(2021, 4, 12)]

        The second is for use when sorting a sequence of objects that have
        :class:`DateTime` objects as attributes. This example sorts the
        ``CarePlan`` objects by the care plan's period's start date:

        >>> sorted(care_plan_list, key=DateTime.sort_key("period.start"))

        In this example, ``sorted()`` passes each item in ``care_plan_list`` to
        the ``sort_key`` static method, which first gets the ``period``
        attribute of the item, then gets the ``start`` attribute of the period.
        Finally, the year, month, day, and other values are returned to
        ``sorted()``, which does the appropriate sorting on those values.

        :param attr_path: A attribute "path" to the :class:`DateTime` object to
            be used as the basis for sorting, such as ``"period.start"``.
        :return: A function identifying values to use for sorting.
        """
        i = itemgetter(0, 1, 2, 3, 4, 5, 6)
        if attr_path is None:
            return i

        def caller(obj):
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
            if not isinstance(obj, DateTime):
                raise TypeError(
                    f"attr_path must lead to an instance of DateTime, not {type(obj)}"
                )
            return i(obj)

        return caller

    def _cmp(self, other: ComparableTypes):
        if not isinstance(other, (DateTime, datetime, date)):
            raise TypeError(f"Cannot compare DateTime and {type(other)}")

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
            print("Doing a base compare")
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

        # If we've reached this point, self has time values and other must be a DateTime
        # or datetime object, meaning the __sub__ operation from the parent class should
        # succeed.
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

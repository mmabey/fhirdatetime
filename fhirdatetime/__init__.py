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

from __future__ import annotations

import re
from datetime import MAXYEAR, MINYEAR, UTC, date, datetime, tzinfo as tzinfo_
from operator import itemgetter
from typing import TYPE_CHECKING, Self, SupportsIndex, TypeAlias, overload

from ._datetime import (
    _check_int_field,
    _cmp,
    _Date,
    _DateTime,
    _days_in_month,
    _format_offset,
    _format_time,
)

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["FhirDate", "FhirDateTime", "__version__"]
__version__ = "0.2.0"

DATE_FIELDS = ("year", "month", "day")
TIME_FIELDS = ("hour", "minute", "second", "microsecond")
_y_pat = re.compile(r"^(\d{4})$")
_ym_pat = re.compile(r"^(\d{4})-(\d{2})$")
_ymd_pat = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_y_format = "{_year:04d}"
_ym_format = _y_format + "-{_month:02d}"
_ymd_format = _ym_format + "-{_day:02d}"

# Indexes used by __getitem__ / sort_key() to expose fields positionally.
_IDX_YEAR = 0
_IDX_MONTH = 1
_IDX_DAY = 2
_IDX_HOUR = 3
_IDX_MINUTE = 4
_IDX_SECOND = 5
_IDX_MICROSECOND = 6

_MAX_MONTH = 12
_MAX_HOUR = 23
_MAX_MINUTE = 59
_MAX_SECOND = 59
_MAX_MICROSECOND = 999_999

# A date/time field that may be unpopulated, cascading down from month
# through tzinfo (second/microsecond/fold are never unpopulated — they
# default to 0, not None).
_Field: TypeAlias = int | None
# What `_check_date_fields` validates and returns, in (year, month, day) order.
DateFields: TypeAlias = tuple[int, _Field, _Field]
# What `_check_time_fields` validates and returns, in (hour, minute, second,
# microsecond, tzinfo, fold) order.
TimeFields: TypeAlias = tuple[_Field, _Field, int, int, tzinfo_ | None, int]
# The `year` positional accepted by `FhirDate.__new__`/`__init__`: an
# explicit year, an ISO string to parse, or an existing date to copy from.
DateArg: TypeAlias = int | str | date
# The `year` positional accepted by `FhirDateTime.__new__`/`__init__`: an
# explicit year, an ISO string to parse, or an existing date/datetime to
# copy from.
YearArg: TypeAlias = int | str | datetime | date
# What `sort_key()`'s returned callable produces: -1 stands in for
# unpopulated fields.
SortableFields: TypeAlias = tuple[int, ...]


def _check_date_fields(year: int, month: _Field, day: _Field) -> DateFields:
    # Customized from version in datetime.
    # Year checks
    year = _check_int_field(year)
    if not MINYEAR <= year <= MAXYEAR:
        msg = f"year must be in {MINYEAR}..{MAXYEAR}"
        raise ValueError(msg, year)

    # Month checks
    if month is not None:
        month = _check_int_field(month)
        if not 1 <= month <= _MAX_MONTH:
            msg = f"month must be in 1..{_MAX_MONTH}"
            raise ValueError(msg, month)

    # Day checks
    if day is not None:
        if month is None:
            msg = "Cannot specify day without month"
            raise ValueError(msg)
        day = _check_int_field(day)
        dim = _days_in_month(year, month)
        if not 1 <= day <= dim:
            msg = f"day must be in 1..{dim}"
            raise ValueError(msg, day)

    return year, month, day


def _check_time_fields(  # noqa: C901, PLR0913, PLR0917
    day: _Field,
    hour: _Field,
    minute: _Field,
    second: int,
    microsecond: int,
    tzinfo: tzinfo_ | None,
    fold: int,
) -> TimeFields:
    # Hour checks
    if hour is not None:
        if day is None:
            msg = "Cannot specify hour without day"
            raise ValueError(msg)
        hour = _check_int_field(hour)
        if not 0 <= hour <= _MAX_HOUR:
            msg = f"hour must be in 0..{_MAX_HOUR}"
            raise ValueError(msg, hour)

    # Minute checks
    if minute is not None:
        if hour is None:
            msg = "Cannot specify minute without hour"
            raise ValueError(msg)
        minute = _check_int_field(minute)
        if not 0 <= minute <= _MAX_MINUTE:
            msg = f"minute must be in 0..{_MAX_MINUTE}"
            raise ValueError(msg, minute)

    # Hour + Minute checks
    if hour is None and minute is not None:
        msg = "If hour is None, minute must also be None"
        raise ValueError(msg)
    if minute is None and hour is not None:
        msg = "If minute is None, hour must also be None"
        raise ValueError(msg)
    if tzinfo is not None and hour is None:
        msg = "Cannot specify timezone without hour and minute"
        raise ValueError(msg)

    # Second checks
    second = _check_int_field(second)
    if not 0 <= second <= _MAX_SECOND:
        msg = f"second must be in 0..{_MAX_SECOND}"
        raise ValueError(msg, second)

    # Microsecond, fold checks
    microsecond = _check_int_field(microsecond)
    if not 0 <= microsecond <= _MAX_MICROSECOND:
        msg = f"microsecond must be in 0..{_MAX_MICROSECOND}"
        raise ValueError(msg, microsecond)
    if fold not in (0, 1):
        msg = "fold must be either 0 or 1"
        raise ValueError(msg, fold)

    return hour, minute, second, microsecond, tzinfo, fold


class FhirDate(_Date, date):
    """Type for representing date values from FHIR data."""

    def __new__(cls, year: DateArg, *_: object, **__: object) -> Self:
        """Start creating FhirDate instance."""
        # Give date.__new__() an arbitrary date to pass its value checks
        return date.__new__(cls, 1, 1, 1)

    def __init__(self, year: DateArg, month: int | None = None, day: int | None = None) -> None:
        """Create new FhirDate instance.

        :param year: Only required value [1, 9999].
        :param month: Optional [1-12].
        :param day: Optional [1-31].
        :returns: New instance of FhirDate.
        """
        if isinstance(year, (datetime, date)):
            self._replace_with(year)
            return
        if isinstance(year, str):
            dt = FhirDateTime.fromisoformat(year)
            self._replace_with(dt)
            return

        # Check values are within acceptable ranges
        year, month, day = _check_date_fields(year, month, day)
        _Date.__init__(self, year, month, day)

    def isoformat(self) -> str:
        """Return the date formatted according to ISO.

        The full format looks like 'YYYY-MM-DD'. By default, any missing part
        is omitted.
        """
        if self._month is None:
            fmt = _y_format
        elif self._day is None:
            fmt = _ym_format
        else:
            fmt = _ymd_format

        return fmt.format(**self.__dict__)

    @classmethod
    def fromisoformat(cls, date_string: str) -> FhirDate:
        """Construct a FhirDate from the output of FhirDate.isoformat()."""
        for pat in (_y_pat, _ym_pat, _ymd_pat):
            m = re.match(pat, date_string)
            if m:
                return FhirDate(*(int(p) for p in m.groups()))
        msg = "Unknown date format."
        raise ValueError(msg)

    @staticmethod
    def from_native(other: date) -> FhirDate:
        """Create instance from standard lib date obj."""
        d = FhirDate(1)  # Just an arbitrary year
        d._replace_with(other)
        return d

    def _replace_with(self, other: ComparableDateTypes) -> None:
        if not isinstance(other, (FhirDate, date)):
            msg = f"Can only create FhirDate from date types, got {type(other).__name__}"
            raise TypeError(msg)
        self._year = other.year
        self._month = other.month
        self._day = other.day

    @staticmethod
    @overload
    def sort_key(attr_path: None = None) -> Callable[[FhirDate], SortableFields]: ...
    @staticmethod
    @overload
    def sort_key(attr_path: str) -> Callable[[object], SortableFields]: ...
    @staticmethod
    def sort_key(
        attr_path: str | None = None,
    ) -> Callable[[FhirDate], SortableFields] | Callable[[object], SortableFields]:
        """Create a function appropriate for use as a sorting key.

        .. important:: When there is ambiguity due to one :class:`FhirDate`
            object storing less-granular data than another (e.g.,
            ``FhirDate(2021)`` vs. ``FhirDate(2021, 4)``), objects with missing
            values will be ordered *before* those with more granular values
            that would otherwise be considered equivalent when using the ``==``
            operator.

        When you need to sort a sequence of either :class:`FhirDate` objects or
        object that *contain* a :class:`FhirDate` object, this function will
        make it easier to sort the items properly.

        There are two ways to use this function. The first is intended for use
        when sorting a sequence of :class:`FhirDate` objects, something like
        this (notice that ``sort_key()`` is called with no parameters):

        >>> sorted(
        ...     [FhirDate(2021, 4), FhirDate(2021), FhirDate(2021, 4, 12)],
        ...     key=FhirDate.sort_key()
        ... )
        [FhirDate(2021), FhirDate(2021, 4), FhirDate(2021, 4, 12)]

        The second is for use when sorting a sequence of objects that have
        :class:`FhirDate` objects as attributes. This example sorts the
        ``CarePlan`` objects by the care plan's period's start date:

        >>> goal_list = [...]  # See tests/test_sorting.py for full examples
        >>> sorted(goal_list, key=FhirDate.sort_key("startDate"))

        In this example, ``sorted()`` passes each item in ``goal_list`` to the
        ``sort_key`` static method, which  gets the ``startDate`` attribute of
        the goal. Finally, the year, month, and day are returned to
        ``sorted()``, which does the appropriate sorting on those values.

        :param attr_path: A attribute "path" to the :class:`FhirDate` object to
            be used as the basis for sorting, such as ``"startDate"``.
        :return: A function identifying values to use for sorting.
        """
        i = itemgetter(_IDX_YEAR, _IDX_MONTH, _IDX_DAY)
        if attr_path is None:
            return i

        def caller(obj: object) -> SortableFields:
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
            if not isinstance(obj, FhirDate):
                msg = f"attr_path must lead to an instance of FhirDate, not {type(obj).__name__}"
                raise TypeError(msg)
            return i(obj)

        return caller

    def _cmp(self, other: ComparableDateTypes) -> int:
        if not isinstance(other, (FhirDate, date)):
            msg = f"Cannot compare FhirDate and {type(other).__name__}"
            raise TypeError(msg)

        for f in DATE_FIELDS:
            my = getattr(self, f, None)
            ot = getattr(other, f, None)
            if None in {my, ot}:
                return 0
            c = _cmp(my, ot)
            if c != 0:
                return c
        # Means all fields are the same and non-None
        return 0

    def __eq__(self, other: object) -> bool:
        # Unlike ordering comparisons, == must accept arbitrary objects and
        # defer via NotImplemented rather than raise — otherwise routine
        # operations like `x in some_dict`/`x in some_set` crash instead of
        # just returning False when `x` happens to collide with a
        # FhirDate's hash bucket.
        if not isinstance(other, (FhirDate, date)):
            return NotImplemented
        return self._cmp(other) == 0

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, (FhirDate, date)):
            return NotImplemented
        return self._cmp(other) != 0

    def __le__(self, other: ComparableDateTypes) -> bool:
        return self._cmp(other) <= 0

    def __lt__(self, other: ComparableDateTypes) -> bool:
        return self._cmp(other) < 0

    def __ge__(self, other: ComparableDateTypes) -> bool:
        return self._cmp(other) >= 0

    def __gt__(self, other: ComparableDateTypes) -> bool:
        return self._cmp(other) > 0

    def __hash__(self) -> int:
        """Hash consistently with this class's equality semantics.

        ``_cmp`` only ever reaches a non-ambiguous verdict once it finds a
        populated field on both sides that differs; if either side is
        missing a field, comparison short-circuits to "equal". Year is the
        one field always populated, so any two objects that compare equal
        necessarily share the same year — hashing on year alone satisfies
        ``a == b -> hash(a) == hash(b)``.
        """
        return hash(self._year)

    __str__ = isoformat

    def __repr__(self) -> str:
        """Convert to formal string, for repr()."""
        f = [self._year, self._month, self._day]
        while f[-1] in {0, None}:
            del f[-1]
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}({', '.join(map(str, f))})"

    def __getitem__(self, item: int) -> int:
        if item == _IDX_YEAR:
            val = self.year
        elif item == _IDX_MONTH:
            val = self.month
        elif item == _IDX_DAY:
            val = self.day
        else:
            msg = "Valid indexes are 0-2"
            raise IndexError(msg)

        if val is None:
            # Assume we're accessing for sorting purposes and empty values come first
            val = -1
        return val


class FhirDateTime(FhirDate, _DateTime, datetime):
    """Type for representing datetime values from FHIR data.

    Subclasses :class:`FhirDate` (rather than duplicating its comparison
    operators) since a :class:`FhirDateTime` *is a* :class:`FhirDate` with
    optional time-of-day precision layered on top — ``==``/``<``/etc. are
    inherited from :class:`FhirDate` and dispatch back through this class's
    own :meth:`_cmp` override polymorphically.
    """

    def __new__(cls, year: YearArg, *_: object, **__: object) -> Self:
        """Start creating FhirDateTime instance."""
        # Give datetime.__new__() an arbitrary date to pass its value checks.
        # Must call datetime.__new__ directly rather than super().__new__:
        # FhirDate is next in the MRO and its own __new__ would route through
        # date.__new__ instead, producing a plain date-shaped instance.
        return datetime.__new__(cls, 1, 1, 1)

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        year: YearArg,
        month: int | None = None,
        day: int | None = None,
        hour: int | None = None,
        minute: int | None = None,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: tzinfo_ | None = None,
        *,
        fold: int = 0,
    ) -> None:
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
        year, month, day = _check_date_fields(year, month, day)
        hour, minute, second, microsecond, tzinfo, fold = _check_time_fields(
            day, hour, minute, second, microsecond, tzinfo, fold
        )
        # Must call _DateTime.__init__ directly rather than super().__init__:
        # FhirDate is next in the MRO and its own __init__ only accepts
        # (year, month, day), not the full datetime field set.
        _DateTime.__init__(self, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold)

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
        if None in {self._hour, self._minute}:
            return FhirDate.isoformat(self)

        fmt = _ymd_format + sep + _format_time(self._hour, self._minute, self._second, self._microsecond, timespec)
        s = fmt.format(**self.__dict__)
        off = self.utcoffset()
        tz = _format_offset(off)
        if tz:
            s += tz

        return s

    @classmethod
    def fromisoformat(cls, date_string: str) -> FhirDateTime:
        """Construct a FhirDateTime from the output of FhirDateTime.isoformat()."""
        # Check for shorter formats first. Handled one pattern at a time
        # (rather than looping and unpacking `*groups`) so each call site
        # has a fixed, statically-checkable arity.
        m = re.match(_y_pat, date_string)
        if m:
            return FhirDateTime(int(m[1]))
        m = re.match(_ym_pat, date_string)
        if m:
            return FhirDateTime(int(m[1]), int(m[2]))
        m = re.match(_ymd_pat, date_string)
        if m:
            return FhirDateTime(int(m[1]), int(m[2]), int(m[3]))

        try:
            # FhirDate is next in the MRO and its own fromisoformat only
            # handles the y/ym/ymd patterns already tried above (and would
            # just re-raise ValueError) — skip straight to _DateTime's full
            # ISO-datetime parser. See super()'s docs on __mro__ if this
            # explicit two-arg form is surprising:
            # https://docs.python.org/3/library/functions.html#super
            return super(FhirDate, cls).fromisoformat(date_string)
        except (ValueError, IndexError):
            pass

        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            # These formats need to have the UTC timezone inserted after creation
            try:
                return cls.strptime(date_string, fmt).replace(tzinfo=UTC)
            except ValueError:
                pass

        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%Z", "%Y-%m-%dT%H:%M:%S%Z"):
            try:
                return cls.strptime(date_string, fmt)
            except ValueError as err:
                last_err = err
        raise last_err

    @staticmethod
    def from_native(other: datetime | date) -> FhirDateTime:
        """Create instance from standard lib date or datetime obj."""
        dt = FhirDateTime(1)  # Just an arbitrary year
        dt._replace_with(other)
        return dt

    @classmethod
    def fromtimestamp(cls, t: float, tz: tzinfo_ | None = None) -> FhirDateTime:
        """Construct a FhirDateTime from a POSIX timestamp (like time.time()).

        Delegates to the real :class:`datetime.datetime` implementation
        rather than the vendored ``_DateTime._fromtimestamp`` fold-detection
        logic: when `tz` is given, that logic calls ``tz.fromutc()``, a
        method that reads `tzinfo` off the C-level `datetime` struct
        directly rather than through this class's Python-level `tzinfo`
        property. Since a `FhirDateTime`'s underlying struct fields are
        always the `__new__` placeholder ``(1, 1, 1)`` with no tzinfo, that
        read comes back `None` and `fromutc` raises `ValueError`.
        """
        return cls.from_native(datetime.fromtimestamp(t, tz))

    @classmethod
    def now(cls, tz: tzinfo_ | None = None) -> FhirDateTime:
        """Construct a FhirDateTime for the current date and time.

        See :meth:`fromtimestamp` for why this delegates to the real
        :class:`datetime.datetime` instead of the vendored implementation.
        """
        return cls.from_native(datetime.now(tz))

    def __reduce_ex__(self, protocol: SupportsIndex) -> tuple[type[Self], tuple[str]]:
        """Support pickling and :func:`copy.deepcopy`.

        The vendored ``_DateTime.__reduce_ex__`` produces a `bytes` state
        blob shaped for `datetime.__setstate__`, which this class's
        `__init__` doesn't understand (it only accepts `int`, `str`, or
        `date`/`datetime` for `year`). Round-trip through `isoformat`
        instead, since `fromisoformat` is already guaranteed to reconstruct
        any value `isoformat` can produce. Note this loses `fold`, which
        `isoformat` doesn't encode -- an acceptable tradeoff since FHIR data
        has no concept of DST-transition ambiguity.
        """
        del protocol
        return self.__class__, (self.isoformat(),)

    def _replace_with(self, other: ComparableDateTimeTypes) -> None:
        if not isinstance(other, (FhirDateTime, date, datetime)):
            msg = f"Can only create FhirDateTime from date, datetime types, got {type(other).__name__}"
            raise TypeError(msg)
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
    @overload
    def sort_key(attr_path: None = None) -> Callable[[FhirDateTime], SortableFields]: ...
    @staticmethod
    @overload
    def sort_key(attr_path: str) -> Callable[[object], SortableFields]: ...
    @staticmethod
    def sort_key(  # ty: ignore[invalid-method-override]
        attr_path: str | None = None,
    ) -> Callable[[FhirDateTime], SortableFields] | Callable[[object], SortableFields]:
        """Create a function appropriate for use as a sorting key.

        This narrows :meth:`FhirDate.sort_key`'s ``Callable[[FhirDate], ...]``
        return type to ``Callable[[FhirDateTime], ...]``, which is technically
        an LSP violation -- but it reflects a real runtime restriction, not
        just a typing choice: the returned callable's ``attr_path`` form
        needs hour/minute/second/microsecond, so it genuinely rejects a
        plain (non-``FhirDateTime``) ``FhirDate`` via the ``isinstance``
        check below, same as the type says.

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
        when sorting a sequence of :class:`FhirDateTime` objects, something
        like this (notice that ``sort_key()`` is called with no parameters):

        >>> sorted(
        ...     [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
        ...     key=FhirDateTime.sort_key()
        ... )
        [FhirDateTime(2021), FhirDateTime(2021, 4), FhirDateTime(2021, 4, 12)]

        The second is for use when sorting a sequence of objects that have
        :class:`FhirDateTime` objects as attributes. This example sorts the
        ``CarePlan`` objects by the care plan's period's start date:

        >>> care_plan_list = [...]  # See tests/test_sorting.py for full examples
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
        i = itemgetter(
            _IDX_YEAR,
            _IDX_MONTH,
            _IDX_DAY,
            _IDX_HOUR,
            _IDX_MINUTE,
            _IDX_SECOND,
            _IDX_MICROSECOND,
        )
        if attr_path is None:
            return i

        def caller(obj: object) -> SortableFields:
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
            if not isinstance(obj, FhirDateTime):
                msg = f"attr_path must lead to an instance of FhirDateTime, not {type(obj).__name__}"
                raise TypeError(msg)
            return i(obj)

        return caller

    def _cmp(self, other: ComparableDateTimeTypes, allow_mixed: bool = False) -> int:
        # allow_mixed is accepted (but unused) purely to match the base class's
        # signature (_DateTime._cmp) for Liskov substitutability; our
        # naive/aware handling doesn't need the distinction it exists for
        # since we already treat any unpopulated field as an ambiguous match.
        del allow_mixed
        if not isinstance(other, (FhirDateTime, FhirDate, datetime, date)):
            msg = f"Cannot compare FhirDateTime and {type(other).__name__}"
            raise TypeError(msg)

        if not isinstance(other, (FhirDateTime, datetime)):
            # A plain `date` has no tzinfo, so it can never disagree with
            # self on UTC offset.
            base_compare = True
        else:
            mytz = self.tzinfo
            ottz = other.tzinfo
            if mytz is ottz or None in {mytz, ottz}:
                base_compare = True
            else:
                myoff = self.utcoffset()
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
        return (diff and 1) or 0

    def __str__(self) -> str:
        """Convert to string, for str().

        Explicit override needed even though it's otherwise identical to
        the inherited behavior: ``FhirDate`` binds ``__str__ = isoformat``
        directly to its own (date-only) function object, and since
        ``FhirDate`` precedes ``_DateTime`` in this class's MRO, that alias
        would shadow ``_DateTime.__str__``'s polymorphic
        ``self.isoformat(sep=" ")`` call, silently truncating the time
        portion of every value.
        """
        return self.isoformat(sep=" ")

    def __repr__(self) -> str:
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
        s = f"{self.__class__.__module__}.{self.__class__.__qualname__}({', '.join(map(str, f))})"
        if self._tzinfo is not None:
            s = f"{s[:-1]}, tzinfo={self._tzinfo!r})"
        if self._fold:
            s = f"{s[:-1]}, fold=1)"
        return s

    def __getitem__(self, item: int) -> int:
        if item == _IDX_YEAR:
            val = self.year
        elif item == _IDX_MONTH:
            val = self.month
        elif item == _IDX_DAY:
            val = self.day
        elif item == _IDX_HOUR:
            val = self.hour
        elif item == _IDX_MINUTE:
            val = self.minute
        elif item == _IDX_SECOND:
            val = self.second
        elif item == _IDX_MICROSECOND:
            val = self.microsecond
        else:
            msg = "Valid indexes are 0-6"
            raise IndexError(msg)

        if val is None:
            # Assume we're accessing for sorting purposes and empty values come first
            val = -1
        return val


# Defined after both classes since `X | Y` is a runtime expression, not a
# deferred annotation (`from __future__ import annotations` only defers
# annotations, not plain assignments) -- it needs FhirDate/FhirDateTime to
# already exist. Used as annotations elsewhere in this module, which *are*
# deferred, so the forward references there are fine regardless of order.
ComparableDateTypes = FhirDate | date
ComparableDateTimeTypes = FhirDateTime | FhirDate | datetime | date

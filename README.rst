``fhirdatetime``: Flexible ``datetime`` Alternative
===================================================

.. image:: https://readthedocs.org/projects/fhirdatetime/badge/?version=latest
   :target: https://fhirdatetime.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/fhirdatetime.svg
   :target: https://pypi.python.org/pypi/fhirdatetime

.. image:: https://github.com/mmabey/fhirdatetime/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/mmabey/fhirdatetime/actions/workflows/ci.yml

.. image:: https://coveralls.io/repos/github/mmabey/fhirdatetime/badge.svg?branch=main
   :target: https://coveralls.io/github/mmabey/fhirdatetime?branch=main

.. image:: https://img.shields.io/badge/code%20style-ruff-000000.svg
   :target: https://github.com/astral-sh/ruff


``date``/``datetime``-compatible classes for FHIR date/datetime values.

The `FHIR specification <https://www.hl7.org/fhir/>`_ from HL7 is "a
standard for health care data exchange." The FHIR spec includes
`date <https://www.hl7.org/fhir/datatypes.html#date>`_ and
`datetime <https://www.hl7.org/fhir/datatypes.html#dateTime>`_ data types
that provide more flexibility than the standard Python ``date`` and
``datetime`` types. This makes sense when you consider a patient may
report to their provider that they have experience a particular symptom
since a particular year without knowing the month or day of onset.

This library provides two classes: ``FhirDate``, for FHIR's ``date`` type
(year, year-month, or year-month-day precision), and ``FhirDateTime``, for
FHIR's ``dateTime`` type (everything ``FhirDate`` supports, plus an
optional time-of-day and timezone). ``FhirDateTime`` *is a* ``FhirDate``
(it subclasses it), so anywhere a ``FhirDate`` is expected -- comparisons,
sorting, type checks -- a ``FhirDateTime`` works too.


Installation
------------

Install ``fhirdatetime`` using pip::

    pip install fhirdatetime


Usage
-----

Creation
********

Both classes are designed to be used to store date/datetime values from FHIR
payloads (which are JSON strings), so you can create instances from ``str``
values:

>>> FhirDate("2021-03-15")
fhirdatetime.FhirDate(2021, 3, 15)
>>> FhirDateTime("2021-03-15T20:54:00+00:00")
fhirdatetime.FhirDateTime(2021, 3, 15, 20, 54, tzinfo=datetime.timezone.utc)

You can also convert native ``date`` and ``datetime`` objects directly:

>>> FhirDate(date(2021, 3, 15))
fhirdatetime.FhirDate(2021, 3, 15)
>>> FhirDateTime(datetime(2021, 3, 15, 20, 54, tzinfo=timezone.utc))
fhirdatetime.FhirDateTime(2021, 3, 15, 20, 54, tzinfo=datetime.timezone.utc)

Note that ``FhirDateTime`` requires a timezone whenever a time is given, per
the FHIR ``dateTime`` spec -- there's no such thing as an hour/minute with no
offset in FHIR. Values with no time at all (like the ``FhirDate`` examples
above, or a date-only ``FhirDateTime("2021-03-15")``) never need one.

One purpose of this library is to allow flexibility in granularity without
sacrificing the ability to compare (using <, >, ==, etc.) against objects
of the same type as well as native ``date`` and ``datetime`` objects.


Comparison
**********

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

Since ``FhirDateTime`` *is a* ``FhirDate``, the two compare against each
other the same way:

>>> FhirDateTime(2021, 3, 15) == FhirDate(2021, 3, 15)
True


Sorting
*******

Both classes have a ``sort_key()`` class method for sorting a sequence of
``FhirDate``/``FhirDateTime`` objects -- or objects that *contain* one --
including handling the ambiguity that comes with mixed-granularity values:

>>> sorted(
...     [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
...     key=FhirDateTime.sort_key()
... )
[fhirdatetime.FhirDateTime(2021), fhirdatetime.FhirDateTime(2021, 4), fhirdatetime.FhirDateTime(2021, 4, 12)]

See the `full Sorting guide
<https://fhirdatetime.readthedocs.io/en/latest/sorting.html>`_ in the docs
for sorting by an attribute path (e.g. sorting FHIR resources by
``period.start``) and the exact ordering rules for ambiguous comparisons.


License
-------

This project is licensed under the MIT license.

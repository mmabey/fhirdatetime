``fhirdatetime``: Flexible ``datetime`` Alternative
===================================================

.. image:: https://img.shields.io/pypi/v/fhirdatetime.svg
        :target: https://pypi.python.org/pypi/fhirdatetime

.. image:: https://travis-ci.com/mmabey/fhirdatetime.svg?branch=main
    :target: https://travis-ci.com/mmabey/fhirdatetime

.. image:: https://coveralls.io/repos/github/mmabey/fhirdatetime/badge.svg?branch=main
    :target: https://coveralls.io/github/mmabey/fhirdatetime?branch=main

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


A ``datetime``-compatible class for FHIR date/datetime values.

The `FHIR specification <https://www.hl7.org/fhir/>`_ from HL7 is "a
standard for health care data exchange." The FHIR spec includes
`date <https://www.hl7.org/fhir/datatypes.html#date>`_ and
`datetime <https://www.hl7.org/fhir/datatypes.html#dateTime>`_ data types
that provide more flexibility than the standard Python ``date`` and
``datetime`` types. This makes sense when you consider a patient may
report to their provider that they have experience a particular symptom
since a particular year without knowing the month or day of onset.


Installation
------------

Install ``fhirdatetime`` using pip::

    pip install fhirdatetime


Usage
-----

Creation
********

The ``fhirdatetime.DateTime`` class is designed to be used to store date/datetime values
from FHIR payloads (which are JSON strings), you can create instances from ``str``
values:

>>> DateTime("2021-03-15")
fhirdatetime.DateTime(2021, 3, 15)

You can also convert native ``date`` and ``datetime`` objects directly:

>>> DateTime(date(2021, 3, 15))
fhirdatetime.DateTime(2021, 3, 15)
>>> DateTime(datetime(2021, 3, 15, 20, 54))
fhirdatetime.DateTime(2021, 3, 15, 20, 54)

One purpose of this library is to allow flexibility in granularity without
sacrificing the ability to compare (using <, >, ==, etc.) against objects
of the same type as well as native ``date`` and ``datetime`` objects.


Comparison
**********

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


Sorting
*******

.. important:: When there is ambiguity due to one ``DateTime`` object
    storing less-granular data than another (e.g., ``DateTime(2021)``
    vs. ``DateTime(2021, 4)``), objects with missing values will be
    ordered *before* those with more granular values that would
    otherwise be considered equivalent when using the ``==`` operator.

When you need to sort a sequence of either ``DateTime`` objects or
object that *contain* a ``DateTime`` object, the ``DateTime.sort_key()``
function will make it easier to sort the items properly.

There are two ways to use this function. The first is intended for use
when sorting a sequence of ``DateTime`` objects, something like
this (notice that ``sort_key()`` is called with no parameters):

>>> sorted(
...     [DateTime(2021, 4), DateTime(2021), DateTime(2021, 4, 12)],
...     key=DateTime.sort_key()
... )
[DateTime(2021), DateTime(2021, 4), DateTime(2021, 4, 12)]

The second is for use when sorting a sequence of objects that have
``DateTime`` objects as attributes. This example sorts the
``CarePlan`` [#care_ref]_ objects by the care plan's period's start date:

>>> sorted(care_plan_list, key=DateTime.sort_key("period.start"))

In this example, ``sorted()`` passes each item in ``care_plan_list`` to
the ``sort_key`` static method, which first gets the ``period``
attribute of the item, then gets the ``start`` attribute of the period.
Finally, the year, month, day, and other values are returned to
``sorted()``, which does the appropriate sorting on those values.

If neither of these use cases of the ``sort_key()`` function apply to what you
need to do, you can always use a custom lambda to do your sorting. For example, the
following is equivalent to the care plan sorting example:

>>> sorted(care_plan_list, key=lambda x: DateTime.sort_key(x.period.start))


License
-------

This project is licensed under the MIT license.


-------


.. [#care_ref] Take a look at the ``fhir.resources`` `definition of a CarePlan
   here <https://github.com/nazrulworld/fhir.resources/blob/master/fhir/resources/careplan.py>`_
   to get a better idea of what is going on in the example.

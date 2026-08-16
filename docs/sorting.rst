Sorting
=======

.. important:: When there is ambiguity due to one ``FhirDateTime`` object
    storing less-granular data than another (e.g., ``FhirDateTime(2021)``
    vs. ``FhirDateTime(2021, 4)``), objects with missing values will be
    ordered *before* those with more granular values that would
    otherwise be considered equivalent when using the ``==`` operator.
    The same applies to ``FhirDate``.

When you need to sort a sequence of either ``FhirDateTime``/``FhirDate``
objects or objects that *contain* one, the ``sort_key()`` class method
(available on both classes) will make it easier to sort the items
properly.

There are two ways to use this function. The first is intended for use
when sorting a sequence of ``FhirDateTime`` objects, something like
this (notice that ``sort_key()`` is called with no parameters):

>>> sorted(
...     [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
...     key=FhirDateTime.sort_key()
... )
[fhirdatetime.FhirDateTime(2021), fhirdatetime.FhirDateTime(2021, 4), fhirdatetime.FhirDateTime(2021, 4, 12)]

The second is for use when sorting a sequence of objects that have
``FhirDateTime`` objects as attributes. This example sorts the
``CarePlan`` [#care_ref]_ objects by the care plan's period's start date:

>>> sorted(care_plan_list, key=FhirDateTime.sort_key("period.start"))

In this example, ``sorted()`` passes each item in ``care_plan_list`` to
the ``sort_key`` static method, which first gets the ``period``
attribute of the item, then gets the ``start`` attribute of the period.
Finally, the year, month, day, and other values are returned to
``sorted()``, which does the appropriate sorting on those values.

If neither of these use cases of the ``sort_key()`` function apply to what you
need to do, you can always use a custom lambda to do your sorting. For example, the
following is equivalent to the care plan sorting example:

>>> sorted(care_plan_list, key=lambda x: FhirDateTime.sort_key(x.period.start))

``FhirDate.sort_key()`` works the same way, for sequences of ``FhirDate``
objects (or objects containing them) instead:

>>> sorted(
...     [FhirDate(2021, 4), FhirDate(2021), FhirDate(2021, 4, 12)],
...     key=FhirDate.sort_key()
... )
[fhirdatetime.FhirDate(2021), fhirdatetime.FhirDate(2021, 4), fhirdatetime.FhirDate(2021, 4, 12)]


.. [#care_ref] Take a look at the ``fhir.resources`` `definition of a CarePlan
   here <https://github.com/nazrulworld/fhir.resources/blob/master/fhir/resources/careplan.py>`_
   to get a better idea of what is going on in the example.

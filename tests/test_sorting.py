# -*- coding: utf-8 -*-
"""Test parameters of creating FhirDateTime objects."""

from collections import namedtuple

import pytest

from fhirdatetime import FhirDateTime

CarePlan = namedtuple("CarePlan", ["period"])
Period = namedtuple("Period", ["start", "end"])


@pytest.mark.parametrize(
    "pre_sort, post_sort",
    [
        (
            [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
            [FhirDateTime(2021), FhirDateTime(2021, 4), FhirDateTime(2021, 4, 12)],
        ),
    ],
)
def test_sorting_top_level(pre_sort, post_sort):
    """Test sorting of a list of just FhirDateTime objects."""
    assert sorted(pre_sort, key=FhirDateTime.sort_key()) == post_sort


@pytest.mark.parametrize(
    "pre_sort, post_sort, obj_path",
    [
        (
            [  # Pre-sort
                CarePlan(Period(start=FhirDateTime(2021, 4), end=None)),
                CarePlan(Period(start=FhirDateTime(2021), end=None)),
                CarePlan(Period(start=FhirDateTime(2021, 4, 12), end=None)),
            ],
            [  # Post-sort
                CarePlan(Period(start=FhirDateTime(2021), end=None)),
                CarePlan(Period(start=FhirDateTime(2021, 4), end=None)),
                CarePlan(Period(start=FhirDateTime(2021, 4, 12), end=None)),
            ],
            "period.start",
        ),
    ],
)
def test_sorting_embedded(pre_sort, post_sort, obj_path):
    """Test sorting of a list of objects that contain FhirDateTime objects."""
    assert sorted(pre_sort, key=FhirDateTime.sort_key(obj_path)) == post_sort

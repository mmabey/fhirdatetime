# -*- coding: utf-8 -*-
"""Test parameters of creating DateTime objects."""

from collections import namedtuple

import pytest

from fhirdatetime import DateTime

CarePlan = namedtuple("CarePlan", ["period"])
Period = namedtuple("Period", ["start", "end"])


@pytest.mark.parametrize(
    "pre_sort, post_sort",
    [
        (
            [DateTime(2021, 4), DateTime(2021), DateTime(2021, 4, 12)],
            [DateTime(2021), DateTime(2021, 4), DateTime(2021, 4, 12)],
        ),
    ],
)
def test_sorting_top_level(pre_sort, post_sort):
    """Test sorting of a list of just DateTime objects."""
    assert sorted(pre_sort, key=DateTime.sort_key()) == post_sort


@pytest.mark.parametrize(
    "pre_sort, post_sort, obj_path",
    [
        (
            [  # Pre-sort
                CarePlan(Period(start=DateTime(2021, 4), end=None)),
                CarePlan(Period(start=DateTime(2021), end=None)),
                CarePlan(Period(start=DateTime(2021, 4, 12), end=None)),
            ],
            [  # Post-sort
                CarePlan(Period(start=DateTime(2021), end=None)),
                CarePlan(Period(start=DateTime(2021, 4), end=None)),
                CarePlan(Period(start=DateTime(2021, 4, 12), end=None)),
            ],
            "period.start",
        ),
    ],
)
def test_sorting_embedded(pre_sort, post_sort, obj_path):
    """Test sorting of a list of objects that contain DateTime objects."""
    assert sorted(pre_sort, key=DateTime.sort_key(obj_path)) == post_sort

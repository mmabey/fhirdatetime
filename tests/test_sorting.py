"""Test parameters of creating FhirDateTime objects."""

from __future__ import annotations

from typing import NamedTuple

import pytest

from fhirdatetime import FhirDateTime


class Period(NamedTuple):
    """Minimal stand-in for a FHIR Period, for sort_key() path traversal tests."""

    start: FhirDateTime | None
    end: FhirDateTime | None


class CarePlan(NamedTuple):
    """Minimal stand-in for a FHIR CarePlan, for sort_key() path traversal tests."""

    period: Period


@pytest.mark.parametrize(
    ("pre_sort", "post_sort"),
    [
        (
            [FhirDateTime(2021, 4), FhirDateTime(2021), FhirDateTime(2021, 4, 12)],
            [FhirDateTime(2021), FhirDateTime(2021, 4), FhirDateTime(2021, 4, 12)],
        ),
    ],
)
def test_sorting_top_level(pre_sort: list[FhirDateTime], post_sort: list[FhirDateTime]) -> None:
    """Test sorting of a list of just FhirDateTime objects."""
    assert sorted(pre_sort, key=FhirDateTime.sort_key()) == post_sort


@pytest.mark.parametrize(
    ("pre_sort", "post_sort", "obj_path"),
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
def test_sorting_embedded(pre_sort: list[CarePlan], post_sort: list[CarePlan], obj_path: str) -> None:
    """Test sorting of a list of objects that contain FhirDateTime objects."""
    assert sorted(pre_sort, key=FhirDateTime.sort_key(obj_path)) == post_sort

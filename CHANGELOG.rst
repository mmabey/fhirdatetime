Changelog
=========

All notable changes to this project are documented here. Versions follow
the tags published to PyPI.

Unreleased
----------

- Added ``FhirDate``, for FHIR's ``date`` type. ``FhirDateTime`` now
  subclasses it, sharing comparison/hashing/sorting logic instead of
  duplicating it.
- ``FhirDateTime`` now requires a timezone whenever a time is specified,
  matching the FHIR ``dateTime`` grammar (there's no such thing as a
  naive or offset-less time in FHIR). This applies to every construction
  path, including ``now()``/``fromtimestamp()``/``from_native()``, and is
  a breaking change for any code constructing a naive, time-bearing
  ``FhirDateTime``. ``utcnow()``/``utcfromtimestamp()`` now attach UTC
  automatically rather than raising, since they have no ``tz`` parameter
  a caller could otherwise supply.
- ``fromisoformat()`` now accepts a FHIR-legal leap second (``:60``) by
  normalizing it to ``:59`` on parse; direct construction with
  ``second=60`` still raises.
- Fixed pickling/``copy``/``deepcopy`` being broken for every ``FhirDate``
  instance.
- Fixed ``real_date - fhir_date`` (and the ``FhirDateTime`` equivalent)
  silently returning a wrong ``timedelta`` instead of raising or
  computing correctly.
- Fixed arithmetic (``+``/``-``) on a partial-precision ``FhirDate``/
  ``FhirDateTime`` raising a confusing internal ``TypeError`` instead of
  a clear one.
- Fixed ``FhirDate.min``/``.max`` (and the ``FhirDateTime`` equivalents)
  returning instances of the private vendored base type instead of the
  public class.
- Re-wired the Read the Docs integration (the previous GitHub webhook had
  been silently failing since 2021); docs now build automatically again.
- ``main`` now auto-tags and publishes a release on every push that bumps
  the version in ``pyproject.toml``, instead of requiring a manually
  pushed tag.

0.2.0 (2026-08-16)
------------------

- Migrated the build system from Poetry to ``uv``; bumped the minimum
  supported Python to 3.11.
- Replaced isort/black/flake8/darglint with ``ruff`` for linting and
  formatting, and added ``ty`` for type checking.
- Fixed ``FhirDateTime`` being unhashable (missing ``__hash__``).
- Fixed ``__eq__``/``__ne__`` raising ``TypeError`` instead of returning
  ``NotImplemented`` for non-comparable types.
- Migrated CI/CD from Travis CI to GitHub Actions, including PyPI trusted
  publishing (OIDC) for releases.
- Fixed ``README.rst``/``docs/index.rst`` duplication by single-sourcing
  the docs homepage from the README.
- Added ``.readthedocs.yaml`` for Read the Docs builds.
- Added a ``CHANGELOG``.
- Fixed ``FhirDateTime.strptime``/``fromisoformat`` on Python 3.14, where
  CPython renamed the internal ``_strptime`` function it relied on. Added
  Python 3.14 support.
- Added PSF license attribution for ``fhirdatetime/_datetime.py``, which
  is adapted from CPython's ``Lib/datetime.py``; package license changed
  from ``MIT`` to the SPDX expression ``MIT AND PSF-2.0``.
- Fixed pickling/``copy.deepcopy`` being broken for every ``FhirDateTime``
  instance.
- Fixed ``FhirDateTime.fromtimestamp()``/``now()`` raising ``ValueError``
  whenever a timezone was passed.
- Significantly expanded test coverage, closing `#2
  <https://github.com/mmabey/fhirdatetime/issues/2>`_.

0.1.0b8 (2021-04-27)
--------------------

- Fixed ISO-format decoding problems.

0.1.0b6 (2021-04-27)
--------------------

- Added more test coverage and fixed documentation issues.
- Linked documentation to Read the Docs.

0.1.0b5 (2021-04-26)
--------------------

- Fixed problems caused by private properties.

0.1.0b3 (2021-04-26)
--------------------

- Renamed the ``DateTime`` class to ``FhirDateTime``.
- Avoided calling ``datetime.__new__`` directly.

0.1.0b2 (2021-04-22)
--------------------

- Added a datetime format that was previously omitted.

0.1.0b1 (2021-04-20)
--------------------

- Initial beta release: the ``FhirDateTime`` class, sorting helpers,
  documentation, and Travis CI/PyPI publishing setup.

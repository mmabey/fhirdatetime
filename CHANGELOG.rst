Changelog
=========

All notable changes to this project are documented here. Versions follow
the tags published to PyPI.

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

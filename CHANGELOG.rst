Changelog
=========

All notable changes to this project are documented here. Versions follow
the tags published to PyPI.

Unreleased
----------

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

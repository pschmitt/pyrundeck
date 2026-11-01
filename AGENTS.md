# Agent notes

This archived Python package provides a client for the Rundeck REST API. Keep
maintenance changes narrow and preserve the existing public API.

- The CI lint workflow uses the shared
  [ci-workflows](https://github.com/pschmitt/ci-workflows) Python lint action.
- Before changing CI, check for a reusable workflow or action there and
  preserve the caller's existing behavior and check coverage.
- There is no dedicated test suite in this repository. Check any behavior
  changes against the Rundeck API version and examples documented in `README.md`.
- The PyPI workflow runs only for version tags; do not create tags as part of
  ordinary development.

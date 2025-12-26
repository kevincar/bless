Read the Docs
=============

This project is configured for Read the Docs using the `.readthedocs.yaml`
file in the repository root. The documentation build uses:

- `docs/conf.py` for Sphinx configuration
- `docs/requirements.txt` for build dependencies

To publish:

1. Push the repository to a public or private Git host supported by Read the
   Docs.
2. Create a Read the Docs project pointing at the repository.
3. Ensure the default branch builds successfully.

The Read the Docs build configuration lives in `.readthedocs.yaml`.

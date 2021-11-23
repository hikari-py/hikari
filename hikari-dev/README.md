# hikari-dev

This is a mock package to install development dependencies for `hikari`. The aim of this package is to provide specific
versions for the development utilities to ensure cross-compatibility on all machines as well as in CI.

### How to install

The general syntax is:

```bash
pip install ./hikari-dev[<options>]
```

Where `<options>` is a coma-seperated list of what dependencies to install, which are automatically collected from the
different requirement files in this directory. Below you can find the list of available options.

### Available options

- `all`: Install all development dependencies
- `codespell`: Install codespell
- `docs`: Install documentation generator dependencies
- `flake8`: Install flake8 and its plugins
- `formatting`: Install formatting tools
- `mypy`: Install mypy
- `pyright`: Install pyright
- `nox`: Install nox
- `pytest`: Install pytest
- `safety`: Install safety
- `towncrier`: Install towncrier

# hikari

A Python Discord API framework for CPython 3.6, CPython 3.7, CPython 3.8, and PyPy 3.6. Designed for ease of use,
customization, and sane defaults.

## Development

### Tox

This project uses tox to automate several things in CI in such a way that you can replicate running the pipelines locally.
To run the pipeline, ensure you have an appropriate version of python installed, then run `pip install tox` and run
`tox` from the command line. For basic testing, and before committing a change, this will most likely be all you need
to do. This will run all tasks except the reformatter, repeating for every Python environment that exists that is detected.

### Running jobs separately

| Command                           | Description                                                                      |
|:----------------------------------|:---------------------------------------------------------------------------------|
| `tox`                             | Run all jobs.                                                                    |
| `tox -e py`                       | Run unit tests for the default system Python (use py37 or py38 for specificity). |
| `tox -e docs`                     | Generate documentation in `/public/html` and `/public/latex`                     |
| `tox -e sast`                     | Run static application security tests.                                           |
| `tox -e formatcheck`              | Ensure code is formatted correctly, or error.                                    |
| `tox -e reformat`                 | Reformat all source files, tests, and Python configurations.                     |                                                     

### Pytest without tox

If you want to run Pytest alone, that is fine too. Just run `pytest`.

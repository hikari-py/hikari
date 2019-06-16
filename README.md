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

Run `tox -lv` to see the jobs that can be run.                                               

> Tox is failing regarding some file with an arbitrary name not existing!

Make sure a directory called `public` exists and try again.

### Testing all environments

If you don't want to have several versions of Python installed, I have added a set of Dockerfiles in `.ci/local-test-runners` 
to do this for you. Just `cd` into that directory and run the container. An example of running the Python3.6 test suite
for Hikari would be:

```bash
docker-compose build py36
docker-compose run py36
```

The environments supported are listed in the `docker-compose.yml`.

One can run all suites at once using the following:

```bash
docker-compose build --parallel
docker-compose up
docker-compose down
```

It is worth noting that the `hikari` and `hikari_tests` are mounted as read-only volumes. If you change the
code, you do not need to rebuild: just restart the container. This has the side effect that tests may not
create `__pycache__` or write out files.

### Pytest without tox

If you want to run Pytest alone, that is fine too. Just run `pytest`.

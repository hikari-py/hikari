# hikari

A Python Discord API framework for CPython 3.6, CPython 3.7, CPython 3.8, and PyPy 3.6. Designed for ease of use,
customization, and sane defaults.

----

## Contributing to Hikari: what you need to know.

The following lists some useful details that you should read before contributing to Hikari. You should also read
the [contribution guidelines and agreement](CONTRIBUTING.md) before going any further.

### CI: a quick TL;DR

This project uses continuous integration (CI) heavily. This is a set of jobs configured to run in response to any
commit or change that is made. Each set of jobs makes up a "pipeline" which runs once per commit. The idea is to run
unit tests in all targeted Python environments (currently CPython 3.6 though 3.8, and PyPy3.6), analyse code coverage
of tests, perform SAST, test that the project can be installed using `pip`, generate any documentation, 
and finally deploy new code to PyPi so that users can install it easily. This means if you upload untested or broken
code, the pipeline will fail and you will be blocked from merging any pull request or deploying the code until it is
fixed. CI enables us to ensure code works before hitting the user's machine, and acts as a proof of concept that this
code does what it is supposed to do correctly.

### Poetry

Build management uses the new standardized [pyproject.toml](pyproject.toml) build specification. We use [poetry](https://poetry.eustace.io/)
to manage our dependencies, versions, and deployments. You will need to have poetry installed by running
`pip install poetry` from the command line before working with Hikari.

To use hikari in your own projects, poetry is not required.

Poetry will manage creating and running virtual environments for you. Simply run `poetry install -vvv` or `poetry update`
to initially install and update dependencies respectively.

### Testing

To ensure that nothing gets broken or is deployed in a buggy state, we require that all functionality
in this API have 100% test coverage. Tests mock internal states of dependencies to enable us to focus directly
on writing unit tests.

#### Pytest

Hikari uses [Pytest](https://docs.pytest.org/en/latest/) for all testing, and uses several plugins that can be found
listed inside the [pyproject.toml](pyproject.toml) to enable coverage and other helpful bits and pieces. Mocking is done
using [asynctest](https://github.com/Martiusweb/asynctest) to allow mocking of coroutines easily. 

#### Nox

This project uses [nox](https://nox.thea.codes/en/stable/) to automate several things in CI in such a way that you 
can replicate running the pipelines locally. This is a great way of running your tests in the exact same sandbox that is
used during our CI pipelines!

To run the pipeline, ensure you have an appropriate version of python installed, then invoke 
`poetry run nox` from the command line. 
For basic testing, and before committing a change, this will most likely be all you need to run. 
This will run all tasks except the reformatter, repeating for every Python environment that exists that is detected.

##### Running jobs separately

Run `nox -l` to see the jobs that can be run. For example, to only run documentation generation, one should run 
`nox -s sphinx`.

#### Testing all environments at once

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

#### Pytest without nox

If you want to run Pytest alone, that is fine too. Just run `poetry run pytest hikari_tests`.

### Code style

You MUST ensure your code is formatted in the [black](https://github.com/python/black) code style. If you fail to do 
this, then you will find that the pipelines fail. This is done on purpose. Any reformatting any contributor performs
should be expected to only change the code that they are working on, and not any other files. We benefit from this as it
keeps our diffs pure and able to point to the commit that last changed functionality in the file.

Settings for black are specified in [pyproject.toml](pyproject.toml). You just need to install black with 
`poetry install black` and then run `poetry run black`.

### SAST

Static Application Security Testing is performed on every commit. This checks for common security risks in the code base
and will abort the pipeline if any issue is found. We do this using [bandit](https://github.com/PyCQA/bandit). This tool
can be run using `poetry install bandit`, followed by `poetry run bandit`. A nox pipeline also exists for this.

### Documentation

Documentation is generated using [sphinx](http://www.sphinx-doc.org/en/master/). This can be run with 
`poetry run nox -s sphinx`, and will produce HTML output in the `public` directory that will be created inside this repo.

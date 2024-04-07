# Hikari contribution guidelines

First off, we would like to thank you for taking the time to help improve Hikari, it's greatly appreciated. We have
some contribution guidelines that you should follow to ensure that your contribution is at its best.

# Code of conduct

Hikari has a code of conduct that must be followed at all times by all the members of the project. Breaking the code
of conduct can lead to a ban from the project and a report to GitHub.

You can read the code of conduct [here](https://github.com/hikari-py/hikari/blob/master/CODE_OF_CONDUCT.md).

# Versioning scheme

This project follows the versioning scheme stated by [PEP 440](https://www.python.org/dev/peps/pep-0440/).

The development version number is increased automatically after each release in the `master` branch in the master
repository.

Please also refer to the [Semantic Versioning specification](https://semver.org/) for more information.

# Deprecation process

The removal or renaming of anything facing the public facing API must go through a deprecation process, which should
match that of the versioning scheme. There are utilities under `hikari.internal.deprecation` to aid with it.

# Towncrier

To aid with the generation of `CHANGELOG.md` as well as the releases changelog we use `towncrier`.

You will need to install `towncrier` and `hikari` from source before making changelog additions.
```bash
pip install -r dev-requirements/towncrier.txt 
pip install -e .
```

For every pull request made to this project, there should be a short explanation of the change under `changes/`
with the following format: `{pull_request_number}.{type}.md`,

Possible types are:

- `feature`: Signifying a new feature.
- `bugfix`: Signifying a bugfix.
- `documentation`: Signifying a documentation improvement.
- `removal`: Signifying a deprecation or removal of public API.

For changes that do not fall under any of the above cases, please specify the lack of the changelog in the pull request
description so that a maintainer can skip the job that checks for newly added fragments.

Best way to create the fragments is to run `towncrier create {pull_request_number}.{type}.md` after creating the
pull request, edit the created file and committing the changes.

Multiple fragment types can be created per pull request if it covers multiple areas.

# Branches

We would like to keep consistency in naming branches in the remote.

To push branches directly to the remote, you will have to name them like this:
  - `feature/issue-number-small-info-on-branch`
    - This should be used for branches that require more tasks to merge into before going as one MR into `master`.
  - `bugfix/issue-number-small-info-on-branch`
    - This should be used for bugfixes.
  - `task/issue-number-small-info-on-branch`
    - This should be the default for any commit that doesn't fall in any of the cases above.

`issue-number` is optional (only use if issue exists) and can be left out. `small-info-on-branch` should be replaced
with a small description of the branch.

# Nox

We have nox to help out with running pipelines locally and provides some helpful functionality.

You will need to install `nox` locally before running any pipelines.
```bash
pip install -r dev-requirements.txt
```

Nox is similar to tox, but uses a pure Python configuration instead of an INI based configuration. Nox and tox are
both tools for generating virtual environments and running commands in those environments. Examples of usage include
installing, configuring, and running flake8, running pytest, etc.

You can check all the available nox commands by running `nox -l`.

Before committing we recommend you to run `nox` to run all important pipelines and make sure the pipelines won't fail.

You may run a single pipeline with `nox -s name` or multiple pipelines with `nox -s name1 name3 name9`.

# Pipelines

We have several jobs to ensure that the code is at its best that in can be.

This includes:
  - `test`
    - Run tests and installation of the package on different OS's and python versions.
  - `linting`
    - Linting (`flake8`), type checking (`mypy`), safety (`safety`) and spelling (`codespell`).
  - `twemoji`
    - Force test all discord emojis.
  - `pages`
    - Generate webpage + documentation.

All jobs will need to succeed before anything gets merged.

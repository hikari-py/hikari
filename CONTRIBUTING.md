# Hikari contribution guidelines

First off, we would like to thank you for taking the time to help improve Hikari, it's greatly appreciated. We have some contribution guidelines that you should follow to ensure that your contribution is at it's best.

# Branches

We would like to keep consistency in how branches are named.

**This should be followed to ensure no issues when specific jobs run.**
**Your merge request could be closed if a developer/maintainer think it's risky due to pipelines failing.**

To push branches directly to the remote, you will have to name them like this:
  - `task/issue-number-small-info-on-branch`
    - This should be the default for any commit that doesnt fall in any of the cases under.
  - `feature/issue-number-small-info-on-branch`
    - This should be used for branches that require more tasks to merge into before going as one MR into `development`.
  - `bugfix/issue-number-small-info-on-branch`
    - This should be used for bugfixes.

`issue-number` is optional (only use if issue exists) and can be left out. `small-info-on-branch` should be replaced with a small description of the branch.

# Nox

We have nox to help out with running pipelines locally and provides some helpfull functionality.

You can check all the available nox commands by running `nox -l`.

Before commiting we recomend you to run `nox` to run all important pipelines and make sure the pipelines wont fail.

# Pipelines

We have several jobs to ensure that the code is at its best that in can be.

This includes:
  - `install`
    - Test installation.
  - `flake8`
    - Linting.
  - `mypy`
    - Type checking.
  - `safety`
    - Vulnerability checking.
  - `twemoji-mapping`
    - Force test all discord emojis (will only run when a file regarding emojis has been changed).
  - `pdoc3`
    - Generate documentation.
  - `pages`
    - Generate final documentation.
  - `deploy`
    - Deployment to pypi (will only run on `staging` and `master`).

All jobs will need to succeed before anything gets merged.

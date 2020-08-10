# Hikari contribution guidelines

First off, we would like to thank you for taking the time to help improve Hikari, it's greatly appreciated. We have some contribution guidelines that you should follow to ensure that your contribution is at it's best.

# Branches

We would like to keep consistency in how branches are named.

**This should be followed to ensure no issues when specific jobs run.**
**Your merge request could be closed if a developer/maintainer think it's risky due to pipelines failing.**

To push branches directly to the remote, you will have to name them like this:
  - `task/issue-number-small-info-on-branch`
    - This should be the default for any commit that doesnt fall in any of the cases under
  - `feature/issue-number-small-info-on-branch`
    - This should be used for branches that require more tasks to merge into before going as one MR into `development`
  - `bugfix/issue-number-small-info-on-branch`
    - This should be used for bugfixes.

`issue-number` is optional (only use if issue exists) and can be left out. `small-info-on-branch` should be replaced with a small description of the branch

# Nox

We have nox to help out with running pipelines locally and provides some helpfull functionality.

You can check all the available nox commands by running `nox -l`.

Before commiting we recomend you to run `nox` to run all important pipelines and make sure the pipelines wont fail.

# Pipelines

We have several jobs to ensure that the code is at its best that in can be.

This includes:
  - `install`
    - Test installation
  - `flake8`
    - Linting
  - `mypy`
    - Type checking
  - `safety`
    - Vulnerability checking
  - `twemoji-mapping`
    - Force test all discord emojis (will only run when a file regarding emojis has been changed)
  - `pdoc3`
    - Generate documentation
  - `pages`
    - Generate final documentation
  - `deploy`
    - Deployment to pypi (will only run on `staging` and `master`)

All jobs will need to succeed before anything gets merged.

# Code of Conduct

## Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

## Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

## Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at nekoka.tt@outlook.com. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/

Local Test Runners
==================

This contains several Dockerfiles and a compose for simulating the GitLab CI environments locally to quickly verify
unit tests work on all environments without building Python first.

Examples of usage:

- docker-compose build --parallel
- docker-compose run pypy3
- docker-compose run py36

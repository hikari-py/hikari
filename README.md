# hikari - ci/docker-containers

This is an orphan branch that contains build scripts to generate any containers used by the API's pipeline.

Currently this provides:

- `nekokatt/stackless-python-hikari:3.8.0b3` - Stackless Python 3.8.0b3 for AMD64.

## Submitting updates or new images

1. Create a dockerfile in the appropriate place.
2. Amend `.travis.yml` on this branch to build said image as part of the build matrix.
3. Create a PR and add @Nekokatt as a reviewer.

Once the job has run, you should be able to amend the master pipelines with a job that pulls one of these images in.

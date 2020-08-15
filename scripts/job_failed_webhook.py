import os

import requests

webhook_url = os.environ["WEBHOOK_URL"]
build_no = os.environ["TRAVIS_BUILD_NUMBER"]
build_url = os.environ["TRAVIS_BUILD_WEB_URL"]
build_commit = os.environ["TRAVIS_COMMIT"]
short_build_commit = build_commit[:8]

build_type = {
    "push": "new commit",
    "pull_request": "pull request",
    "api": "api-triggered job",
    "cron": "scheduled job",
}.get(raw_build_type := os.getenv("TRAVIS_EVENT_TYPE"), raw_build_type)

if (pr_no := os.getenv("TRAVIS_PULL_REQUEST", "false")) != "false":

    source_slug = os.environ["TRAVIS_PULL_REQUEST_SLUG"]
    source_branch = os.environ["TRAVIS_PULL_REQUEST_BRANCH"]
    target_slug = os.environ["TRAVIS_REPO_SLUG"]
    target_branch = os.environ["TRAVIS_BRANCH"]

    pr_name = f"!{pr_no} {source_slug}#{source_branch} → {target_slug}#{target_branch}"
    pr_url = f"https://github.com/{target_slug}/pull/{pr_no}"

    author_field = dict(name=pr_name, url=pr_url,)
else:
    author_field = None

job_name = os.environ["TRAVIS_JOB_NAME"]
job_no = os.environ["TRAVIS_JOB_NUMBER"]
job_url = os.environ["TRAVIS_JOB_WEB_URL"]
job_os = os.environ["TRAVIS_OS_NAME"]
job_dist = os.environ["TRAVIS_DIST"]
job_arch = os.environ["TRAVIS_CPU_ARCH"]

payload = dict(
    username="Travis CI",
    embeds=[
        dict(
            title=f"Job #{job_no} failed for {build_type} (`{short_build_commit}`)",
            url=build_url,
            author=author_field,
            color=0xFF0000,
            footer=dict(text=job_name),
        )
    ],
)

with requests.post(webhook_url, json=payload) as resp:
    print("POST", payload)
    print(resp.status_code, resp.reason)
    try:
        print(resp.json())
    except:
        print(resp.content)


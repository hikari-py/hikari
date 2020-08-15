import os
import textwrap

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


commit_message = textwrap.TextWrapper(width=80, max_lines=4).wrap(os.environ["TRAVIS_COMMIT_MESSAGE"])[0]

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

payload = dict(
    username="Travis CI",
    embeds=[
        dict(
            title=f"Build #{build_no} succeeded for {build_type} (`{short_build_commit}`)",
            description=commit_message,
            author=author_field,
            color=0x00FF00,
            url=build_url,
            footer=dict(text="Travis CI"),
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

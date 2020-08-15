import os

import requests

webhook_url = os.environ["WEBHOOK_URL"]
success = os.environ["TRAVIS_TEST_RESULT"] == "0"
job_no = os.environ["TRAVIS_BUILD_NUMBER"]
job_url = os.environ["TRAVIS_BUILD_WEB_URL"]
job_commit = os.environ["TRAVIS_COMMIT"][:8]

if (pr_no := os.getenv("TRAVIS_PULL_REQUEST", "false")) != "false":
    ignore = False

    source_slug = os.environ["TRAVIS_PULL_REQUEST_SLUG"]
    source_branch = os.environ["TRAVIS_PULL_REQUEST_BRANCH"]
    target_slug = os.environ["TRAVIS_REPO_SLUG"]
    target_branch = os.environ["TRAVIS_BRANCH"]

    pr = f"[!{pr_no} {source_slug}#{source_branch} → {target_slug}#{target_branch}]"
    pr += f"(https://github.com/{target_slug}/pull/{pr_no})"
else:
    ignore = os.environ["TRAVIS_BRANCH"] != "master"
    pr = ""

result = "SUCCEEDED" if success else "FAILED"

message = f"Build [{job_no}]({job_url}) for {job_commit} {result}!" + "\n" + pr

if not ignore:
    print("Sending payload :: ", message)
    requests.post(webhook_url, {"content": message, "username": "Travis CI"})
else:
    print("Not sending payload.")

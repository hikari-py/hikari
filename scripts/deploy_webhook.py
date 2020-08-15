import os

import requests

webhook_url = os.environ["WEBHOOK_URL"]
tag = os.environ["TRAVIS_TAG"]
build_no = os.environ["TRAVIS_BUILD_NUMBER"]
commit_sha = os.environ["TRAVIS_COMMIT"]

payload = {
    "username": "Travis CI",
    "embed": {
        "title": f"{tag} has been deployed to PyPI",
        "color": 0x663399,
        "description": "Install it now!",
        "footer": {
            "text": f"#{build_no} | {commit_sha}"
        }
    }
}

requests.post(webhook_url, data=payload)

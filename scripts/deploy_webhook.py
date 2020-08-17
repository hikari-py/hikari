import os

import requests

if os.getenv("TRAVIS_TAG"):
    webhook_url = os.environ["DEPLOY_WEBHOOK_URL"]
    tag = os.environ["TRAVIS_TAG"]
    build_no = os.environ["TRAVIS_BUILD_NUMBER"]
    commit_sha = os.environ["TRAVIS_COMMIT"]

    payload = dict(
        username="Travis CI",
        embeds=[
            dict(
                title=f"{tag} has been deployed to PyPI",
                color=0x663399,
                description="Install it now!",
                footer=dict(text=f"#{build_no} | {commit_sha}"),
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
else:
    print("Skipping webhook, not on a tag.")

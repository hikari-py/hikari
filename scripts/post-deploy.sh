#!/bin/sh
VERSION=${TRAVIS_TAG}
REF=${TRAVIS_COMMIT}

#git config user.name "Nekokatt"
#git config user.email "69713762+nekokatt@users.noreply.github.com"
#
#git remote set-url origin https://nekokatt:${GITHUB_TOKEN}github.com/${TRAVIS_REPO_SLUG}
#git fetch origin master
#git checkout master
#
#echo "Bumping repository version to ${VERSION} (ref: ${REF})"
#sed "s|^__version__.*|__version__ = \"${VERSION}\"|g" -i hikari/_about.py
#sed "s|^__git_sha1__.*|__git_sha1__ = \"${REF}\"|g" -i hikari/_about.py
#echo "=========================================================================="
#cat hikari/_about.py
#echo "=========================================================================="
#
#git add hikari/_about.py
#git commit hikari/_about.py -m "Updated config version from new release ${VERSION} @ ${REF} [skip ci]"
#git push
## Clear from git-config
#git remote set-url origin https://github.com/${TRAVIS_SLUG}

pip install nox
mkdir public || true
nox --sessions pdoc pages
git branch -D gh-pages || true
git subtree split --prefix public HEAD --branch gh-pages
echo "Deploying pages"
git add -A -n .
echo git commit -am "Deployed pages with ${TRAVIS_COMMIT} [skip ci]"
echo push -f

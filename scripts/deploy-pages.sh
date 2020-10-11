git config user.name "davfsa"
git config user.email "29100934+davfsa@users.noreply.github.com"

rm public -Rf || true
mkdir public
nox --sessions pdoc3 pages
cd public || exit 1
git init

if [ -z ${CI+x} ]; then
    git remote add origin git@github.com:hikari-py/hikari
else
    git remote add origin https://davfsa:${GITHUB_TOKEN}@github.com/${TRAVIS_REPO_SLUG}
fi

git checkout -B gh-pages
git add -Av .
git commit -am "Deployed documentation for ${VERSION}"
git push origin gh-pages --force

git config user.name "Nekokatt"
git config user.email "69713762+nekokatt@users.noreply.github.com"

rm public -Rf || true
mkdir public
nox --sessions pdoc pages
cd public || exit 1
git init

if [ -z ${CI+x} ]; then
    git remote add origin git@github.com:nekokatt/hikari
else
    git remote add origin https://nekokatt:${GITHUB_TOKEN}@github.com/${TRAVIS_REPO_SLUG}
fi

git checkout -B gh-pages
git add -Av .
git commit -am "Deployed documentation for ${VERSION}"
git push origin gh-pages --force

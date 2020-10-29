# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
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

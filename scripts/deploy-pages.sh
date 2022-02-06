# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
set -e

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

if [ -z ${VERSION+x} ]; then echo '$VERSION environment variable is missing' && exit 1; fi
if [ -z "${VERSION}" ]; then echo '$VERSION environment variable is empty' && exit 1; fi
if [ -z ${REF+x} ]; then echo '$REF environment variable is missing' && exit 1; fi
if [ -z "${REF}" ]; then echo '$REF environment variable is empty' && exit 1; fi
if [ -z ${GITHUB_TOKEN+x} ]; then echo '$GITHUB_TOKEN environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TOKEN}" ]; then echo '$GITHUB_TOKEN environment variable is empty' && exit 1; fi
if [ -z ${REPO_SLUG+x} ]; then echo '$REPO_SLUG environment variable is missing' && exit 1; fi
if [ -z "${REPO_SLUG}" ]; then echo '$REPO_SLUG environment variable is empty' && exit 1; fi
if [ -z ${DOCUMENTATION_REPO_SLUG+x} ]; then echo '$DOCUMENTATION_REPO_SLUG environment variable is missing' && exit 1; fi
if [ -z "${DOCUMENTATION_REPO_SLUG}" ]; then echo '$DOCUMENTATION_REPO_SLUG environment variable is empty' && exit 1; fi

if [ "${VERSION}" != "master" ]; then
  regex='__version__: typing\.Final\[str\] = "([^"]*)"'
  if [[ $(cat hikari/_about.py) =~ $regex ]]; then
    if [ "${BASH_REMATCH[1]}" != "${VERSION}" ]; then
      echo "Variable '__version__' does not match the version this deploy is for! [__version__='${BASH_REMATCH[1]}'; VERSION='${VERSION}']" && exit 1
    fi
  else
    echo "Variable '__version__' not found in about!" && exit 1
  fi
fi

rm -rf public
mkdir public

echo "-- Setting __git_sha1__ to '${REF}' --"
sed "/^__git_sha1__.*/, \${s||__git_sha1__: typing.Final[str] = \"${REF}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__git_sha1__' not found in about!" && exit 1)

nox -s pdoc
cd public/docs || exit 1

# We do it here before we create the empty repository
if [ "${REF}" == "MASTER" ]; then
  REF="$(git rev-parse HEAD)"
fi

echo "===== DEPLOYING PAGES ====="
git init
git remote add origin "https://git:${GITHUB_TOKEN}@github.com/${DOCUMENTATION_REPO_SLUG}"

git checkout -B "release/${VERSION}"
git add -Av .
git commit -am "Documentation for ${VERSION} [https://github.com/${REPO_SLUG}/commit/${REF}]"
git push -u origin "release/${VERSION}" -f

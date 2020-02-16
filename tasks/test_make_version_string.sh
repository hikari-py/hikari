#!/bin/bash

try() {
    branch=$1
    pages=$2
    test_version=$3
    TEST_VERSION_STRING_VERSION_LINE="__version__ = \"${test_version}\"" python tasks/make_version_string.py "${branch}" "${pages}"
}

# shellcheck disable=SC2068
assert() {
    expected_version=$1
    shift 3
    actual_version=$(try $@)
    echo -en "\e[0;33m- ($*) results in a version of \e[0;35m${actual_version}\e[0;33m, we expected \e[0;36m${expected_version}\e[0m -- "
    if [[ "${actual_version}" = "${expected_version}" ]]; then
        echo -e "\e[1;32mPASSED\e[0m"
    else
        echo -e "\e[1;31mFAILED\e[0m"
        exit 1
    fi
}

tests() {
    assert 300.300.300.dev when using staging pages 300.300.300.dev
    assert 300.300.300.dev when using staging pages 300.300.300.dev1
    assert 300.300.300.dev when using staging pages 300.300.300.dev9999
    assert 300.300.300.dev when using staging pages 300.300.300
    assert 300.300.300.dev when using staging pages 300.300.300sdasdfgafg
    assert 300.300.dev when using staging pages 300.300
    assert 300.dev when using staging pages 300
    assert 0.0.0.dev when using staging pages ""

    assert 300.300.300.dev1 when using staging no_pages 300.300.300.dev
    assert 300.300.300.dev2 when using staging no_pages 300.300.300.dev1
    assert 300.300.300.dev10000 when using staging no_pages 300.300.300.dev9999
    assert 300.300.301.dev when using staging no_pages 300.300.300
    assert 300.300.300.dev1 when using staging no_pages 300.300.300sdasdfgafg
    assert 300.301.dev when using staging no_pages 300.300
    assert 301.dev when using staging no_pages 300
    assert 0.0.1.dev when using staging no_pages ""

    assert 300.300.300 when using master pages 300.300.300.dev
    assert 300.300.300 when using master pages 300.300.300.dev1
    assert 300.300.300 when using master pages 300.300.300.dev9999
    assert 300.300.300 when using master pages 300.300.300
    assert 300.300.300 when using master pages 300.300.300sdasdfgafg
    assert 300.300 when using master pages 300.300
    assert 300 when using master pages 300
    assert 0.0.0 when using master pages ""

    assert 300.300.300 when using master no_pages 300.300.300.dev
    assert 300.300.300 when using master no_pages 300.300.300.dev1
    assert 300.300.300 when using master no_pages 300.300.300.dev9999
    assert 300.300.300 when using master no_pages 300.300.300
    assert 300.300.300 when using master no_pages 300.300.300sdasdfgafg
    assert 300.300 when using master no_pages 300.300
    assert 300 when using master no_pages 300
    assert 0.0.0 when using master no_pages ""
}

time tests

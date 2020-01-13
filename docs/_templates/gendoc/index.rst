:orphan:

.. image:: https://img.shields.io/discord/574921006817476608.svg?logo=Discord&logoColor=white&label=discord
    :target: https://discord.gg/HMnGbsv
.. image:: https://img.shields.io/lgtm/alerts/gitlab/nekokatt/hikari
    :target: https://lgtm.com/projects/gl/nekokatt/hikari
.. image:: https://img.shields.io/lgtm/grade/python/gitlab/nekokatt/hikari
    :target: https://lgtm.com/projects/gl/nekokatt/hikari?mode=tree
.. image:: https://gitlab.com/nekokatt/hikari/badges/master/coverage.svg
    :target: https://gitlab.com/nekokatt/hikari/pipelines
.. image:: https://img.shields.io/gitlab/pipeline/nekokatt/hikari/master?label=ci%20(master)&logo=gitlab
    :target: https://gitlab.com/nekokatt/hikari/pipelines
.. image:: https://img.shields.io/gitlab/pipeline/nekokatt/hikari/staging?label=ci%20(staging)&logo=gitlab
    :target: https://gitlab.com/nekokatt/hikari/pipelines
.. image:: https://img.shields.io/website/https/nekokatt.gitlab.io/hikari.svg?down_color=red&down_message=not%20building&label=docs%20(master)&logo=gitlab&logoColor=white&up_message=up-to-date
    :target: https://nekokatt.gitlab.io/hikari
.. image:: https://img.shields.io/website/https/nekokatt.gitlab.io/hikari/staging.svg?down_color=red&down_message=not%20building&label=docs%20(staging)&logo=gitlab&logoColor=white&up_message=up-to-date
    :target: https://nekokatt.gitlab.io/hikari/staging
.. image:: https://badgen.net/pypi/v/hikari
    :target: https://pypi.org/project/hikari
.. image:: https://img.shields.io/sourcegraph/rrc/gitlab.com/nekokatt/hikari
    :target: https://sourcegraph.com/gitlab.com/nekokatt/hikari
.. image:: https://img.shields.io/static/v1?label=sourcegraph&message=view%20now!&color=blueviolet&logo=sourcegraph
    :target: https://sourcegraph.com/gitlab.com/nekokatt/hikari

.. image:: https://badgen.net/pypi/license/hikari
.. image:: https://img.shields.io/pypi/implementation/hikari.svg
.. image:: https://img.shields.io/pypi/format/hikari.svg
.. image:: https://img.shields.io/pypi/dm/hikari
.. image:: https://img.shields.io/pypi/status/hikari
.. image:: https://img.shields.io/pypi/pyversions/hikari
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg

Hikari Technical Documentation
##############################

This is for version |version|. |staging_link|

Hikari is licensed under the GNU LGPLv3 https://www.gnu.org/licenses/lgpl-3.0.en.html

Packages and submodules
-----------------------

.. autosummary::
    :toctree: {{documentation_path}}

    {% for m in modules %}{{ m }}
    {% endfor %}

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
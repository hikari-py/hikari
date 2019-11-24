:orphan:

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

.. inheritance-diagram::
    {% for m in modules %}{{ m }}
    {% endfor %}

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

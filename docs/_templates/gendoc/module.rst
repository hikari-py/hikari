:orphan:

.. currentmodule:: {{ module }}

{{ module | underline }}

{% if submodules %}

.. autosummary::
    {% for m in submodules %}{{ m }}
    {% endfor %}
{% endif %}

Overview
--------

.. autosummary::
    {{ module }}
    :members:


Details
-------

.. automodule:: {{ module }}
   :show-inheritance:
   :inherited-members:



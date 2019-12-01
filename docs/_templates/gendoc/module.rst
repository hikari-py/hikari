:orphan:

{{ module }}
{{ rule }}

{% if submodules %}

Submodules
----------

.. autosummary::
    {% for m in submodules %}{{ m }}
    {% endfor %}
{% endif %}

Documentation
-------------

.. automodule:: {{ module }}
    :inherited-members:

:orphan:

{{ module }}
{{ rule }}

{% if submodules %}

Documentation
-------------

.. automodule:: {{ module }}
    :inherited-members:

Submodules
----------

.. autosummary::
    {% for m in submodules %}{{ m }}
    {% endfor %}
{% endif %}


:orphan:

{{ module }}
{{ rule }}

Documentation
-------------

.. automodule:: {{ module }}
    :inherited-members:

{% if submodules %}

Submodules
----------

.. autosummary::
    {% for m in submodules %}{{ m }}
    {% endfor %}
{% endif %}


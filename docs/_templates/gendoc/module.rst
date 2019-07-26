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


.. inheritance-diagram:: {{ module }} {% for m in submodules %}{{ m }} {% endfor %}
    :parts: 1
    :private-bases:


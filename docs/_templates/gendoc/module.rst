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


.. inheritance-diagram:: {{ module }} {% for m in submodules %}{{ m }} {% endfor %}
   :parts: 1
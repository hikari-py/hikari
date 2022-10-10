.. TODO: Remove once https://github.com/readthedocs/sphinx-autoapi/pull/353 is merged

{% if obj.display %}
.. py:{{ obj.type }}:: {{ obj.name }}
   {%- if obj.annotation is not none %}

   :type: {%- if obj.annotation %} {{ obj.annotation }}{%- endif %}

   {%- endif %}

   {%- if obj.value is not none %}

   :value: {% if obj.value is string and obj.value.splitlines()|count > 1 -%}
                Multiline-String

    .. raw:: html

        <details><summary>Show Value</summary>

    .. code-block:: text
        :linenos:

        {{ obj.value|indent(width=8) }}

    .. raw:: html

        </details>

            {%- else -%}
                {{ obj.value|string|truncate(100) }}
            {%- endif %}
   {%- endif %}


   {{ obj.docstring|indent(3) }}
{% endif %}

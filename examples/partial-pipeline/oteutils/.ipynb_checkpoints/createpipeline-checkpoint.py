

# Please connect to: client = OTEPipelines(url='http://localhost:8080') use otelib pypi package
{% for h in hh %}
    {% if h.ft == 'ResourceConfig' %}
        f_{{ loop.index }} = client.create_dataresource(ResourceConfig(configuration={{h.config.configuration}},downloadUrl={{"'" + h.config.downloadUrl + "'"}} ,mediaType={{"'" +h.config.mediaType + "'"}}))
    {% endif %}
    {% if h.ft == 'MappingConfig' %}
         f_{{ loop.index }} = client.create_mapping(MappingConfig(configuration={{h.config.configuration}},mappingType={{"'" + h.config.mappingType + "'"}} ,triples={{h.config.triples }}))
    {% endif %}
    {% if h.ft == 'FunctionConfig' %}
         f_{{ loop.index }} = client.create_function(FunctionConfig(configuration={{h.config.configuration}},functionType={{"'" + h.config.functionType + "'"}}))
    {% endif %}
    {% if h.ft == 'FilterConfig' %}
         f_{{ loop.index }} = client.create_filter(FilterConfig(configuration={{h.config.configuration}},filterType={{"'" + h.config.filterType + "'"}}))
    {% endif %}
{% endfor %}
storedPipeline = {% for i in range(hh|length) %}f_{{ i + 1 }} {% if hh|length > i+1 %} >> {% endif %}  {% endfor %}
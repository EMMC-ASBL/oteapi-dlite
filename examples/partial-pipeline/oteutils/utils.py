from .kb import *
import yaml
from jinja2 import Environment, FileSystemLoader

def fetch_pipeline(PipeAB):
    filters=get_pipeline_filters(PipeAB)
    diction=[]
    for fil in filters:
        hh=get_filter_config(fil)
        y={}
        z={}
        if hh["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"] =='http://onto-ns.com/meta/oteapi#ResourceConfig':
            y['ft']='ResourceConfig'
            z['configuration']=json.loads(get_data_property(hh['http://onto-ns.com/meta/oteapi#configuration']))
            z['downloadUrl']=get_data_property(hh['http://onto-ns.com/meta/oteapi#downloadUrl'])
            z['mediaType']=get_data_property(hh['http://onto-ns.com/meta/oteapi#mediaType'])
            # print(str(z)[1:-1])
            y['config']=z
        if hh["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"] =='http://onto-ns.com/meta/oteapi#MappingConfig':
            y['ft']='MappingConfig'
            z['configuration']=json.loads(get_data_property(hh['http://onto-ns.com/meta/oteapi#configuration']))
            z['mappingType']=get_data_property(hh['http://onto-ns.com/meta/oteapi#mappingType'])
            z['triples']=get_data_property(hh['http://onto-ns.com/meta/oteapi#triples']).replace('{', '[').replace('}', ']')
            y['config']=z
        if hh["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"] =='http://onto-ns.com/meta/oteapi#FunctionConfig':
            y['ft']='FunctionConfig'
            z['configuration']=json.loads(get_data_property(hh['http://onto-ns.com/meta/oteapi#configuration']))
            z['functionType']=get_data_property(hh['http://onto-ns.com/meta/oteapi#functionType'])
            y['config']=z
        if hh["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"] =='http://onto-ns.com/meta/oteapi#FilterConfig':
            y['ft']='FilterConfig'
            z['configuration']=json.loads(get_data_property(hh['http://onto-ns.com/meta/oteapi#configuration']))
            z['filterType']=get_data_property(hh['http://onto-ns.com/meta/oteapi#filterType'])
            y['config']=z

        diction.append(y)

    

    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template("createpipeline.py")
    return template.render(hh=diction)
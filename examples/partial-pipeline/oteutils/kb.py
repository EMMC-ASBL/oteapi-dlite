"""
Utilities
"""
import rdflib
import json
from uuid import uuid4
from SPARQLWrapper import SPARQLWrapper, BASIC, POST, JSON
from otelib import OTEClient

from oteapi.models.genericconfig import AttrDict
from oteapi.models.datacacheconfig import DataCacheConfig
from oteapi.models.filterconfig import FilterConfig
from oteapi.models.functionconfig import FunctionConfig
from oteapi.models.genericconfig import GenericConfig
from oteapi.models.mappingconfig import MappingConfig 
from oteapi.models.resourceconfig import ResourceConfig
from oteapi.models.sessionupdate import SessionUpdate
from oteapi.models.transformationconfig import TransformationConfig
from oteapi.models.triplestoreconfig import TripleStoreConfig
MAP = rdflib.Namespace("http://emmo.info/domain-mappings#")

BASE_URL = "http://localhost:3030"
DATASET = "OTE2"
def _sparql_query(query):
    """ helper function to run SPARQL queries (read only) """
    db = SPARQLWrapper(f"{BASE_URL}/{DATASET}/sparql")

    db.setHTTPAuth(BASIC)
    db.setCredentials("admin", "secret")
    db.setMethod(POST)
    db.setReturnFormat(JSON)
    db.setQuery(query)
    
    try:
        return db.queryAndConvert()        
    except Exception as e:
        print (e)
        
def _update_query(query):
    """ helper function to run SPARQL updates (modify) """
    db = SPARQLWrapper(f"{BASE_URL}/{DATASET}/update")

    db.setHTTPAuth(BASIC)
    db.setCredentials("admin", "secret")
    db.setMethod(POST)
    db.setReturnFormat('json')
    db.queryType = "INSERT"
    db.setQuery(query)
    try:
        return db.query()        
    except Exception as e:
        print (e)
        return None
 
def _insert_data_statements(model):
    data_inserts = []
    props = {}
    for p in model:
        if not p[0] == "description" and not p[1] == None:
            prop_id = str(uuid4())
            props[p[0]] = prop_id

            if (type(p[1]) == AttrDict):
                value = json.dumps(p[1].json())            
            else:
                value = "\"" + str(p[1]) + "\""

            data_inserts.append(f":_{prop_id} rdf:type owl:NamedIndividual")
            data_inserts.append(f":_{prop_id} rdf:type rdfs:Resource")
            data_inserts.append(f":_{prop_id} owl:topDataProperty {value}" )

    classname = model.schema()['title']
    class_id = str(uuid4())
    data_inserts.append(f":_{class_id} rdf:type owl:NamedIndividual")
    data_inserts.append(f":_{class_id} rdf:type :{classname}")
    for prop in props:
        data_inserts.append(f":_{class_id} :{prop} :_{props[prop]}")


    return ".\n".join(data_inserts) + ";", f"<http://onto-ns.com/meta/oteapi#_{class_id}>"


def store_configuration(conf):
    data, classid = _insert_data_statements(conf)

    query = f'''
    PREFIX owl: <http://www.w3.org/2002/07/owl#> 
    PREFIX : <http://onto-ns.com/meta/oteapi#> 
    PREFIX owl: <http://www.w3.org/2002/07/owl#> 
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
    PREFIX xml: <http://www.w3.org/XML/1998/namespace> 
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 

    INSERT DATA {{
            {data}
    }}
    '''
    _update_query(query)
    
    return classid


def find_configuration_by_value(value):
    """
    Query the triplestore for all configurations containing value 'value'
    """   
    query=f"""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT ?configuration ?property WHERE {{  
      ?o owl:topDataProperty "{ value }" .
      ?configuration ?property ?o ;
    }}"""

    ret = _sparql_query(query)

    for r in ret["results"]["bindings"]:
        yield ("<"+r["configuration"]["value"]+">", r["property"]["value"])

def find_pipeline_by_config_iri(value):
    """
    Query the triplestore for all configurations containing value 'value'
    """ 
    iri= list(find_configuration_by_value(value))[0][0]
    # return iri
    query = f"""    
    PREFIX emmo: <http://emmo.info/emmo#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT * WHERE {{    
        ?filter emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204 { iri }
    }}                     

    """
    ret = _sparql_query(query)
    # return ret
    for r in ret["results"]["bindings"]:
        filter1= r["filter"]["value"]
     
    query = f"""    
    PREFIX emmo: <http://emmo.info/emmo#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT * WHERE {{    
        ?pipeline emmo:EMMO_fe63194f_7c04_4dbd_a244_524b38b6699b <{ filter1 }>
    }}                     

    """
    ret = _sparql_query(query)
    # return ret
    for r in ret["results"]["bindings"]:
        return r["pipeline"]["value"]
    
    return None


        
def get_configuration_by_iri(iri):
    
    query = f"""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT ?keyword ?value WHERE {{
      ?o owl:topDataProperty ?value .
      { iri } ?keyword ?o ;
    }}
    """
        
    ret = _sparql_query(query)
    
    data = {}
    for r in ret["results"]["bindings"]:
        kw  = r['keyword']['value']
        val = r['value']['value']
        kw  = kw[kw.find('#')+1:]
        if kw == 'configuration':
            val = json.loads(val)
        data[kw] = val        
    return data
    


_lookup = {
    "http://onto-ns.com/meta/oteapi#DataCacheConfig": DataCacheConfig,
    "http://onto-ns.com/meta/oteapi#FilterConfig": FilterConfig,
    "http://onto-ns.com/meta/oteapi#FunctionConfig": FunctionConfig,
    "http://onto-ns.com/meta/oteapi#GenericConfig": GenericConfig,
    "http://onto-ns.com/meta/oteapi#MappingConfig": MappingConfig,
    "http://onto-ns.com/meta/oteapi#ResourceConfig": ResourceConfig,
    "http://onto-ns.com/meta/oteapi#SessionUpdate": SessionUpdate,
    "http://onto-ns.com/meta/oteapi#TransformationConfig": TransformationConfig,
    "http://onto-ns.com/meta/oteapi#TripleStoreConfig": TripleStoreConfig   
}


def create_configuration(iri, data):   
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT DISTINCT * WHERE {{    
          { iri } rdf:type ?configClass . 
      FILTER(STRSTARTS(STR(?configClass), "http://onto-ns.com/meta/oteapi#"))
    }}
    """
    ret = _sparql_query(query)
    
    
    assert(len(ret["results"]["bindings"]) == 1)
    
    class_iri = ret["results"]["bindings"][0]['configClass']['value']
    Class = _lookup[class_iri]    
    return Class(**data)
    
    
class OTEPipelines:
    """ OTEPipelines is a wrapper to the OTELib 
        with extensions to move filters and configurations
        between client and triplestores.
    """
    
    def __init__(self, url: str) -> None:
        """ Initialize otelib """
        self.client = OTEClient(url)
        self.refs = {}
    
    def create_dataresource(self, config : ResourceConfig):
        resource = self.client.create_dataresource(
            configuration=config.configuration,
            description=config.description,
            downloadUrl=config.downloadUrl,
            mediaType=config.mediaType,
            accessUrl=config.accessUrl,            
            accessService=config.accessService,
            license=config.license,
            accessRights=config.accessRights,
            publisher=config.publisher
        )
        self.refs[resource.strategy_id] = (resource, config, ":DataResourceStrategy",store_configuration(config))        
        return resource
    
    def create_transformation(self, config : TransformationConfig):
        transformation = self.client.create_tranformation(
            configuration=config.configuration,
            description=config.description,
            transformationType=config.transformationType,
            name=config.name,
            due=config.due,
            priority=config.priority,
            secret=config.secret
        )
        self.refs[transformation.strategy_id] = (transformation, config, ":TransformationStrategy",store_configuration(config))
        return transformation

    
    def create_filter(self, config : FilterConfig):
        filter_ = self.client.create_filter(
            configuration=config.configuration,
            description=config.description,
            filterType=config.filterType,
            query=config.query,
            condition=config.condition,
            limit=config.limit
        )
        self.refs[filter_.strategy_id] = (filter_, config,
                                          ":FilterStrategy",store_configuration(config))
        return filter_

    
    def create_mapping(self, config : MappingConfig):
        mapping = self.client.create_mapping(
            configuration=config.configuration,
            description=config.description,
            mappingType=config.mappingType,
            prefixes=config.prefixes,
            triples=config.triples
        )
        self.refs[mapping.strategy_id] = (mapping, config, 
                                          ":MappingStrategy",store_configuration(config))        
        return mapping
      
       
    def create_function(self, config : FunctionConfig):
        func = self.client.create_function(
            configuration=config.configuration,
            description=config.description,
            functionType=config.functionType
        )
        self.refs[func.strategy_id] = (func, config, 
                                       ":FunctionStrategy",store_configuration(config))
        return func
    
    
    def _store_pipeline_data_statements(self, pipeline):
        filter = pipeline
        last = True
        filter_next = None
        data_inserts = []
        pipeline_iri = f":_{str(uuid4())}" 
        data_inserts.append(f"{pipeline_iri} rdf:type :Pipeline")
        while (hasattr(filter, 'input_pipe')):    
            pipe = filter.input_pipe
            filter_iri = f":_{str(uuid4())}"
            if last:
                last = False  
                data_inserts.append(f"{pipeline_iri} emmo:EMMO_c0f48dc6_4a32_4d9a_a956_d68415954a8e {filter_iri}") #hasEndTile (filter_iri is the blanknode!)
                               
            data_inserts.append(f"{filter_iri} emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204 {self.refs[filter.strategy_id][3]}") #hasProperty (map to configuration)
            data_inserts.append(f"{filter_iri} rdf:type :Filter")
            data_inserts.append(f"{filter_iri} :hasId '{filter.strategy_id}'")
            data_inserts.append(f"{filter_iri} :hasImplementation {self.refs[filter.strategy_id][2]}")
            if filter_next:
                data_inserts.append(f"{filter_iri} emmo:EMMO_499e24a5_5072_4c83_8625_fe3f96ae4a8d {filter_next}") #hasNext (temporalnext)

            if hasattr(pipe, 'input'):
                filter = pipe.input
                filter_next=filter_iri
            else:
                data_inserts.append(f"{pipeline_iri} emmo:EMMO_fe63194f_7c04_4dbd_a244_524b38b6699b {filter_iri}") #hasBeginTile
                filter = None     
                
        return ".\n".join(data_inserts) + ";"
 
         
    def store_pipeline(self, pipeline):
        data = self._store_pipeline_data_statements(pipeline) 
        query = f'''

        PREFIX : <http://onto-ns.com/meta/oteapi#> 
        PREFIX emmo: <http://emmo.info/emmo#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#> 
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
        PREFIX xml: <http://www.w3.org/XML/1998/namespace> 
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 

        INSERT DATA {{
                {data}
        }}
        '''
        result = _update_query(query)        
        return result
       
def get_all_pipeline_iris():    
    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT * WHERE {{  
      ?pipeline rdf:type :Pipeline
    }}"""
    
    ret = _sparql_query(query)
    for r in ret["results"]["bindings"]:
        yield (r['pipeline']['value'])
    
def get_filter_config(filter_iri):
    query = f"""
    PREFIX emmo: <http://emmo.info/emmo#>
    SELECT * WHERE {{
        <{ filter_iri }> emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204 ?config
        }}
    """
    ret = _sparql_query(query)
    config_uri=''
    for r in ret["results"]["bindings"]:
        config_uri= r["config"]["value"]
    query2=f"""
    PREFIX emmo: <http://emmo.info/emmo#>
    SELECT * WHERE {{
        <{ config_uri }> ?p ?config_uris
        }}
    """
    ret1 = _sparql_query(query2)
    config_uri={}
    for r1 in ret1["results"]["bindings"]:
        config_uri[r1["p"]["value"]]=r1["config_uris"]["value"]
    return config_uri

def get_data_property(uri):
    query = f"""
    PREFIX emmo: <http://emmo.info/emmo#>
    SELECT * WHERE {{
        <{ uri }> <http://www.w3.org/2002/07/owl#topDataProperty> ?data
        }}
    """
    ret = _sparql_query(query)
    for r in ret["results"]["bindings"]:
        data= r["data"]["value"]
  
        return data

def get_next_filter(filter_iri):
    query = f"""
    PREFIX emmo: <http://emmo.info/emmo#>
    SELECT * WHERE {{
        <{ filter_iri }> emmo:EMMO_499e24a5_5072_4c83_8625_fe3f96ae4a8d ?filter
        }}
    """
    ret = _sparql_query(query)
    for r in ret["results"]["bindings"]:
        return r["filter"]["value"]
    return None
    
def get_pipeline_filters(pipeline_iri):
    query = f"""    
    PREFIX emmo: <http://emmo.info/emmo#>
    PREFIX : <http://onto-ns.com/meta/oteapi#>
    SELECT * WHERE {{    
        <{ pipeline_iri }> emmo:EMMO_fe63194f_7c04_4dbd_a244_524b38b6699b ?filter
    }}                     

    """
   
    ret = _sparql_query(query)
    bindings = ret["results"]["bindings"]
    if len(bindings) > 0:
        filter = bindings[0]["filter"]["value"]    
        filters = [filter]
        next = get_next_filter(filter)
        while next:        
            filters.append(next)
            next = get_next_filter(next)
        return filters
    return None

def get_pipeline_filters_id(pipeline_iri):
    filters=get_pipeline_filters(pipeline_iri)
    filter_ids=[]
    for filter in filters:
        query1 = f"""    
            PREFIX emmo: <http://emmo.info/emmo#>
            PREFIX : <http://onto-ns.com/meta/oteapi#>
            SELECT * WHERE {{    
                <{ filter }> <http://onto-ns.com/meta/oteapi#hasId> ?filter_id
            }}                     

            """
        ret = _sparql_query(query1)
        bindings = ret["results"]["bindings"]
        if len(bindings) > 0:
            filterId = bindings[0]["filter_id"]["value"]
            filter_ids.append(filterId)
    return filter_ids
    return None



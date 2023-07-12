from oteutils.kb import *
from oteutils.utils import *
# Connect to the OTEAPI services (Docker container)
client = OTEPipelines(url='http://localhost:8080')

dataMappings=[
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#InstructName", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#instructName"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#SerialNumber", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#serialNumber"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#DataNumber", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#dataNumber"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Format", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#format"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#ImageName", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#imageName"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#ImageUrl", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#imageUrl"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Directory", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#directory"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Date", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#date"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Time", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#time"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Media", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#media"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#DataSize", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#dataSize"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#PixelSize", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#pixelSize"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#SignalName", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#signalName"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#AcceleratingVoltage", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#acceleratingVoltage"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#DecelerationVoltage", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#decelerationVoltage"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Magnification", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#magnification"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#WorkingDistance", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#workingDistance"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#EmissionCurrent", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#emissionCurrent"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#LensMode", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#lensMode"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#PhotoSize", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#photoSize"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Vacuum", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#vacuum"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#MicronMarker", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#micronMarker"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#SubMagnification", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#subMagnification"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#SubSignalName", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#subSignalName"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#SpecimenBias", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#specimenBias"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#Condencer1", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#condencer1"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#ScanSpeed", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#scanSpeed"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#CalibrationScanSpeed", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#calibrationScanSpeed"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#ColorMode", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#colorMode"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#PolymorphicMode", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#polymorphicMode"),
  ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#LensMagnification", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#lensMagnification")
]

# Create configurations for filters

# Resource Config for mpr files
cansDataConfig = ResourceConfig(    
    downloadUrl="https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/151-partial-pipeline-example/examples/partial-pipeline/data/Hitachi_imageName1.txt",
    mediaType="application/parse-txt",
    configuration={
        "splitBy":"=",
        "metadata": "http://onto-ns.com/meta/matchmaker/demo/0.2/image" ,
        "storage_path": "/dome_demo/models" 
    }
)

cansMprDataParser= client.create_dataresource(cansDataConfig)
createcollectionfilter = FilterConfig(
      filterType="dlite/create-collection",
    description="",
    configuration={},
)
cansDataMappingsMpr = MappingConfig(
    mappingType="mappings",
    triples = dataMappings,
    configuration={
    }     
)
cansMprDataMappings = client.create_mapping(cansDataMappingsMpr)
createCollection=client.create_filter(createcollectionfilter)

generatorMappings=[ ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#imageURL", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#imageUrl"),
                   ("http://onto-ns.com/meta/matchmaker/demo/0.2/image#pixelSIZE", "http://emmo.info/domain-mappings#mapsTo", "http://onto-ns.com/1/sem#pixelSize")]

# Mapping configuration for the mapping filter
generatorMappingConfig = MappingConfig(
    mappingType="mappings",
    triples = generatorMappings,
    configuration={
    }     
)

# Configuration that fetches data and stores to a json file
generatorFilterConfig = FunctionConfig(
    functionType="dlite/translate",
    configuration={'metadata':'http://onto-ns.com/meta/matchmaker/demo/0.1/imageurl',
                    'storage_path':"/dome_demo/models/matchmakerConsumer.json",
                   "fileDestination": "/oteapi-dlite/output_dlite.json"} 
)
generatorMappings= client.create_mapping(generatorMappingConfig)
generatorFilter=client.create_function(generatorFilterConfig)

# Select whether to assemble short or full pipeline:
full_pipeline = True

if(not full_pipeline):
    # Build a short pipeline; this works (returns a collection_id)
    pipeline = cansMprDataParser>>cansMprDataMappings
else:
    # Build a new pipeline by merging the fetched one with the generator Pipeline; this produces
    # the 'siemens' DimensionalityError, visible in the oteapi-services docker container.
    pipeline = cansMprDataParser>>cansMprDataMappings>>generatorMappings>>generatorFilter>>createCollection

# Execute the pipeline
pipeline.get()
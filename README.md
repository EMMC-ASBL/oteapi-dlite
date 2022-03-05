# OTEAPI DLite Plugin

All strategies implemented in this plugin (except for `create_collection`) assumes that you have the UUID of a DLite collection with the key `collection_id` in the `session`:

```python
collection_id = session["collection_id"]
coll = dlite.get_collection(collection_id)
```

A DLite collection stores references to DLite instances and relations between them as RDF triples.
Hence, the collection is a knowledge base for the current use case.

In order to make it easy retrieve the collection id when executing a pipeline, the `get()` method of all filters in this plugin should return the `collection_id`.


Further reading:

- [OTE-API Core Documentation](https://emmc-asbl.github.io/oteapi-core)
- [OTE-API Services Documentation](https://github.com/EMMC-ASBL/oteapi-services)
- [DLite](https://github.com/SINTEF/dlite)


## License and copyright

The OTEAPI DLite Plugin is released under the [MIT license](LICENSE) with copyright &copy; SINTEF.


## Acknowledgment

OTEAPI DLite Plugin has been created via the [cookiecutter](https://cookiecutter.readthedocs.io/) [template for OTE-API plugins](https://github.com/EMMC-ASBL/oteapi-plugin-template).

OTEAPI DLite Plugin has been supported by the following projects:

- **OntoTrans** (2020-2024) that receives funding from the European Union’s Horizon 2020 Research and Innovation Programme, under Grant Agreement n. 862136.

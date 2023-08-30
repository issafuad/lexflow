Basic Usage Pattern
===================

The general usage pattern of LlamaIndex is as follows:

- Load in documents (either manually, or through a data loader)
- Parse the Documents into Nodes
- Construct Index (from Nodes or Documents)
- [Optional, Advanced] Building indices on top of other indices
- Query the index

Load in Documents
-----------------

The first step is to load in data. This data is represented in the form of Document objects. We provide a variety of data loaders which will load in Documents through the ``load_data`` function, e.g.::

   from llama_index import SimpleDirectoryReader

   documents = SimpleDirectoryReader('./data').load_data()

You can also choose to construct documents manually. LlamaIndex exposes the Document struct.::

   from llama_index import Document

   text_list = [text1, text2, ...]
   documents = [Document(text=t) for t in text_list]

A Document represents a lightweight container around the data source. You can now choose to proceed with one of the following steps:

- Feed the Document object directly into the index (see section 3).
- First convert the Document into Node objects (see section 2).

Parse the Documents into Nodes
------------------------------

The next step is to parse these Document objects into Node objects. Nodes represent “chunks” of source Documents, whether that is a text chunk, an image, or more. They also contain metadata and relationship information with other nodes and index structures.

Nodes are a first-class citizen in LlamaIndex. You can choose to define Nodes and all its attributes directly. You may also choose to “parse” source Documents into Nodes through our NodeParser classes.

For instance, you can do::

   from llama_index.node_parser import SimpleNodeParser

   parser = SimpleNodeParser.from_defaults()
   nodes = parser.get_nodes_from_documents(documents)

You can also choose to construct Node objects manually and skip the first section. For instance,::

   from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo

   node1 = TextNode(text="<text_chunk>", id_="<node_id>")
   node2 = TextNode(text="<text_chunk>", id_="<node_id>")
   # set relationships
   node1.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=node2.node_id)
   node2.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=node1.node_id)
   nodes = [node1, node2]

The RelatedNodeInfo class can also store additional metadata if needed::

   node2.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=node1.node_id, metadata={"key": "val"})

Index Construction
------------------

We can now build an index over these Document objects. The simplest high-level abstraction is to load-in the Document objects during index initialization (this is relevant if you came directly from step 1 and skipped step 2).

``from_documents`` also takes an optional argument ``show_progress``. Set it to True to display a progress bar during index construction.::

   from llama_index import VectorStoreIndex

   index = VectorStoreIndex.from_documents(documents)

You can also choose to build an index over a set of Node objects directly (this is a continuation of step 2).::

   from llama_index import VectorStoreIndex

   index = VectorStoreIndex(nodes)

Depending on which index you use, LlamaIndex may make LLM calls in order to build the index.

Reusing Nodes across Index Structures
-------------------------------------

If you have multiple Node objects defined, and wish to share these Node objects across multiple index structures, you can do that. Simply instantiate a StorageContext object, add the Node objects to the underlying DocumentStore, and pass the StorageContext around.::

   from llama_index import StorageContext

   storage_context = StorageContext.from_defaults()
   storage_context.docstore.add_documents(nodes)

   index1 = VectorStoreIndex(nodes, storage_context=storage_context)
   index2 = ListIndex(nodes, storage_context=storage_context)

.. note::

   If the ``storage_context`` argument isn’t specified, then it is implicitly created for each index during index construction. You can access the docstore associated with a given index through ``index.storage_context``.

Inserting Documents or Nodes
----------------------------

You can also take advantage of the insert capability of indices to insert Document objects one at a time instead of during index construction.::

   from llama_index import VectorStoreIndex

   index = VectorStoreIndex([])
   for doc in documents:
       index.insert(doc)

If you want to insert nodes on directly you can use ``insert_nodes`` function instead.::

   from llama_index import VectorStoreIndex

   # nodes: Sequence[Node]
   index = VectorStoreIndex([])
   index.insert_nodes(nodes)

.. seealso::

   See the Document Management How-To for more details on managing documents and an example notebook.

Customizing Documents
---------------------

When creating documents, you can also attach useful metadata. Any metadata added to a document will be copied to the nodes that get created from it.

... (this section seems to be cut off; you may need to complete it based on your full content.)

# Program that creates a Mongo Vector Search Index for RAG queries
from pymongo.mongo_client import MongoClient
from pymongo.operations import SearchIndexModel
import time
import os

# Connect to Atlas and access collection
client = MongoClient(os.environ.get("MONGO_URI"))
database = client["bedrock"]
collection = database["kb"]

# Create index model
search_index_model = SearchIndexModel(
  definition={
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 1024,
        "similarity": "dotProduct",
        "quantization": "scalar"
      }
    ]
  },
  name="vector_index",
  type="vectorSearch"
)

# Create search index
result = collection.create_search_index(model=search_index_model)
print("New search index named " + result + " is building.")

# Sync the index and message when ready
print("Polling to check if the index is ready. This may take up to a minute.")
predicate=None
if predicate is None:
  predicate = lambda index: index.get("queryable") is True
while True:
  indices = list(collection.list_search_indexes(result))
  if len(indices) and predicate(indices[0]):
    break
  time.sleep(5)
print(result + " is ready for querying.")

client.close()

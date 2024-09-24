import certifi
from pymongo import MongoClient

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']

# Function to list all collections in the database
def list_collections():
    collections = db.list_collection_names()

    if collections:
        print("Collections in the database:")
        for collection in collections:
            print(f"- {collection}")
    else:
        print("No collections found in the database.")

# Call the function
list_collections()

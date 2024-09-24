import certifi
from pymongo import MongoClient

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)

# Test the connection
try:
    # Attempt to fetch the server information to verify the connection
    db = client.admin
    server_status = db.command("serverStatus")
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error: {e}")

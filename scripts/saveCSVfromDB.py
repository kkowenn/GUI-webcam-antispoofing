import certifi
import pandas as pd
from pymongo import MongoClient

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']

# Function to display all documents in the database collections and save as CSV
def save_all_data_to_csv():
    collections = db.list_collection_names()

    if collections:
        print("Collections in the database:")
        for collection_name in collections:
            print(f"Processing collection: {collection_name}")

            # Access the collection
            collection = db[collection_name]
            documents = list(collection.find({}))  # Fetch all documents

            if documents:
                # Convert documents to DataFrame
                df = pd.DataFrame(documents)

                # Save DataFrame to CSV file
                csv_filename = f"scripts/exampleOfDatabase{collection_name}.csv"
                df.to_csv(csv_filename, index=False)

                print(f"Data from collection '{collection_name}' saved to {csv_filename}")
            else:
                print(f"No documents found in {collection_name}.")
    else:
        print("No collections found in the database.")

# Call the function
save_all_data_to_csv()

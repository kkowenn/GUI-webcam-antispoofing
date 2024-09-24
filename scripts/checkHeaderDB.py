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


def check_class_field_name(user_id):
    try:
        # Access the specific collection (replace 'attendances' with your collection name if needed)
        db = client['afterfall']  # Replace 'afterfall' with your actual database name if different
        collection = db['attendances']  # Replace 'attendances' with the correct collection name

        # Fetch one document for the user to inspect the field names
        record = collection.find_one({'UserID': user_id})

        if record:
            print(f"Document for UserID {user_id}: {record}")
        else:
            print(f"No records found for UserID {user_id}")

    except Exception as e:
        print(f"Error fetching data for {user_id}: {e}")


# Example usage
check_class_field_name("6420063")  # Replace with the UserID you want to inspect

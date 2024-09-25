import certifi
from pymongo import MongoClient

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']

# Collections
classes_collection = db['classes']

# Function to insert mock class data into the classes collection
def insert_mock_classes():
    """Insert mock classes into the classes collection, skipping existing classes."""
    mock_classes = [
        {"classID": "CSX4212", "className": "Data Analytics"},
        {"classID": "CSX3006", "className": "Programming Languages"},
        {"classID": "CSX4213", "className": "Computer Vision"},
        {"classID": "CSX5010", "className": "Machine Learning"},
        {"classID": "CSX5222", "className": "Cloud Computing"},
        {"classID": "CSX6234", "className": "Artificial Intelligence"}
    ]

    # Iterate through each class and check if it already exists
    for mock_class in mock_classes:
        class_id = mock_class['classID']

        # Check if a class with the same classID already exists in the collection
        if classes_collection.find_one({"classID": class_id}):
            print(f"Class with classID {class_id} already exists, skipping insert.")
        else:
            try:
                # Insert the new class if it doesn't exist
                classes_collection.insert_one(mock_class)
                print(f"Class {mock_class['className']} inserted successfully.")
            except Exception as e:
                print(f"Error inserting class {class_id}: {e}")

# Test simple insertion first to ensure connection and permissions
def test_insert():
    """Test inserting a single document to verify connection and permissions."""
    try:
        classes_collection.insert_one({"classID": "TEST001", "className": "Test Class"})
        print("Test document inserted successfully!")
    except Exception as e:
        print(f"Error during test insert: {e}")

# Main execution
if __name__ == "__main__":
    # First run a simple insert test to verify connectivity
    test_insert()

    # Insert the mock classes into the database
    insert_mock_classes()

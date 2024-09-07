from pymongo import MongoClient
import certifi

def check_mongodb_connection():
    try:
        # Update with your MongoDB credentials
        client = MongoClient(
            'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
            tlsCAFile=certifi.where()
        )

        # Check connection to MongoDB
        client.server_info()  # This will raise an exception if MongoDB is not available
        print("MongoDB is reachable and running.")

        # Access the database and collection
        db = client['afterfall']  # Replace 'afterfall' with your database name
        collection = db['attendance']  # Replace 'attendance' with your collection name

        # Display all attendance records
        attendance_records = list(collection.find())

        if attendance_records:
            print("\nAll Attendance Records in MongoDB:")
            for record in attendance_records:
                print(f"UserID: {record.get('UserID')}, Timestamp: {record.get('attendance')}")
        else:
            print("\nNo attendance records found in the database.")

    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

if __name__ == "__main__":
    check_mongodb_connection()

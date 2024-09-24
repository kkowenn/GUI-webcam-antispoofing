from pymongo import MongoClient
import certifi
import datetime
import pytz

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
        collection = db['attendances']  # Replace 'attendances' with your collection name

        # Display all attendance records
        attendance_records = list(collection.find())

        if attendance_records:
            print("\nAll Attendance Records in MongoDB:")
            thailand_tz = pytz.timezone('Asia/Bangkok')  # Define Thailand timezone

            for record in attendance_records:
                user_id = record.get('UserID', "Unknown")
                timestamps = record.get('attendance', [])

                # Ensure that timestamps is a list
                if isinstance(timestamps, list) and timestamps:
                    print(f"UserID: {user_id}")

                    # Loop through the timestamps
                    for timestamp in timestamps:
                        if isinstance(timestamp, datetime.datetime):
                            if timestamp.tzinfo is None:  # Add timezone info if missing
                                timestamp = pytz.UTC.localize(timestamp)

                            # Convert timestamp to Thailand time
                            timestamp_thailand = timestamp.astimezone(thailand_tz)
                            print(f"  - {timestamp_thailand.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                else:
                    print(f"UserID: {user_id} has no valid attendance records.")
        else:
            print("\nNo attendance records found in the database.")

    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

if __name__ == "__main__":
    check_mongodb_connection()


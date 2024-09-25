import certifi
import random
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']

# Collections
attendances_collection = db['attendances']
classes_collection = db['classes']

# Function to add new user manually
def add_new_user(user_id, class_id, num_attendances=5, mock_datetime=None):
    """Add a new user manually with random attendance for a specific class."""

    # Generate attendance timestamps (using mock datetime if provided)
    attendances = []
    base_time = mock_datetime or datetime.now(pytz.UTC)

    for i in range(num_attendances):
        random_minutes = random.randint(1, 1000)
        attendances.append(base_time - timedelta(minutes=random_minutes))

    # Prepare the new user document
    new_user = {
        "UserID": user_id,
        "attendance": attendances,
        "classID": class_id
    }

    # Insert the new user into the attendances collection
    attendances_collection.insert_one(new_user)
    print(f"New user {user_id} added to class {class_id} with {num_attendances} attendance records.")

# Function to generate random users and classes
def generate_random_user_with_classes(user_id, class_ids, num_classes=2, num_attendances_per_class=5, mock_datetime=None):
    """Generate a random user with attendance records for multiple classes."""

    for class_id in random.sample(class_ids, num_classes):  # Choose random classes
        add_new_user(user_id, class_id, num_attendances_per_class, mock_datetime)

# Mock the current datetime to ensure predictable attendance times
mocked_time = datetime(2024, 9, 25, 15, 30, tzinfo=pytz.UTC)

# Apply the mock for datetime.now to return the mocked_time
with patch('datetime.datetime') as mock_datetime:
    mock_datetime.now.return_value = mocked_time
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    # Add a new user manually with mocked attendance times
    user_id = "6420022"
    class_id = "CSX4212"
    add_new_user(user_id, class_id)

    # Generate a new random user with multiple classes and mocked attendance
    random_user_id = "6420023"
    available_class_ids = ["CSX4212", "CSX3006", "CSX5010"]  # Example class IDs
    generate_random_user_with_classes(random_user_id, available_class_ids)

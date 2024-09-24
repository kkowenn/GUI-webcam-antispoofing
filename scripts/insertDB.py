from pymongo import MongoClient
import certifi
import datetime
import pytz

client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']
collection = db['attendances']

# Get the current time in UTC
timestamp_utc = datetime.datetime.now(pytz.UTC)
thailand_tz = pytz.timezone('Asia/Bangkok')
timestamp_thailand = timestamp_utc.astimezone(thailand_tz)

# Try manually inserting data
user_id = "6420063"
result = collection.update_one(
    {'UserID': user_id},
    {'$push': {'attendance': timestamp_thailand}},
    upsert=True
)

print(f"Insert result: Matched {result.matched_count}, Upserted ID {result.upserted_id}")

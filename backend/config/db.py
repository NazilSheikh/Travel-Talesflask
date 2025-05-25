from mongoengine import connect
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is not set in the environment")
    connect(host=mongo_uri)
    print("✅ MongoDB connected")

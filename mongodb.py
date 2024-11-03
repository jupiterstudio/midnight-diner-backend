from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class MongoDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            mongo_uri = os.getenv("MONGO_URI")
            cls._client = MongoClient(mongo_uri)
            cls._db = cls._client[os.getenv("DB_NAME")]
        return cls._instance

    @property
    def db(self):
        return self._db

    def get_collection(self, collection_name):
        return self._db[collection_name]

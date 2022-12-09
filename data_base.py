"""
This module contains the connection to the database.
"""
import os
import pymongo
from dotenv import load_dotenv


load_dotenv()

def open_connection() -> pymongo.MongoClient:
    """
    Open connection to the database
    """
    return pymongo.MongoClient(os.getenv('DB_CONNECTION_STRING'))


def get_data_base(mongo_client = open_connection(), data_base_name = os.getenv('DB_NAME')):
    """
    Get database
    """
    return mongo_client[data_base_name]


def close_connection(mongo_client = open_connection()):
    """
    Close connection to the database
    """
    mongo_client.close()

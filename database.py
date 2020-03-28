"""
Sets up the database objects
"""
from utils import get_loggers
from pymongo import MongoClient
from yaml import load, FullLoader
from datetime import datetime, timedelta
from time import sleep

with open('config.yaml') as f:
    config = load(f, Loader=FullLoader)

def get_db():
    client = MongoClient(config["db_url"])
    db=client.StockTwits
    return db
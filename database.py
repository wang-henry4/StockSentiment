"""
Sets up the database objects
"""
from pymongo import MongoClient
from yaml import load, FullLoader
with open('config.yaml') as f:
    config = load(f, Loader=FullLoader)

client = MongoClient(config["db_url"])
db=client.StockTwits
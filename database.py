"""
Sets up the database objects
"""
from pymongo import MongoClient
from yaml import load, FullLoader
with open('config.yaml') as f:
    config = load(f, Loader=FullLoader)

client = MongoClient(config["db_url"])
db=client.StockTwits

class Ema_data:
    def __init__(self, size = 288):
        self.max_size = 288
        self._data = [(doc["ema"], doc["end"]) 
            for doc in db.averages.find().sort("end", -1).limit(288)][::-1]
        self.size = len(self._data)

    def update(self):
        latest = db.averages.find_one({"latest": True})
        self._data.append((latest["ema"], latest["end"]))
        if len(self._data) > self.max_size:
            dif = len(self._data) - self.max_size
            self._data = self._data[dif:]
        self.size = len(self._data)

    @property
    def data(self):
        return list(zip(*self._data))

    def __len__(self):
        return self.size
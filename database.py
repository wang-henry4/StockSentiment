"""
Sets up the database objects
"""
from pymongo import MongoClient
from yaml import load, FullLoader
from datetime import datetime, timedelta
from time import sleep
with open('config.yaml') as f:
    config = load(f, Loader=FullLoader)

client = MongoClient(config["db_url"])
db=client.StockTwits
class Avg_calc:
    def __init__(self, window=30, increments=2):
        self.window = timedelta(minutes=window)
        self.increments = increments

    def calc_now(self, ticker="SPY"):
        t =  self.round_time(datetime.utcnow())
        self.update(t, ticker)

    def calc_past(self, ticker="SPY"):
        latest = list(db.averages.find().sort("time", -1).limit(1))[0]["time"]
        latest += self.increments
        while latest <= self.round_time(datetime.utcnow()):
            self.update(latest, ticker)

    def round_time(self, dt):
        if dt.second >= 30:
            dt = dt + timedelta(minutes=1)
        dt = dt.replace(second=0, microsecond=0)
        if dt.minute%self.increments:
            dt = dt.replace(minute=dt.minute//self.increments)
        return dt

    def update(self, time, ticker="SPY"):
        end = time
        start = time - self.window
        ratio = self.calc_avg(start, end, ticker)
        new_doc = {
            "time": end,
            "MovingAvg": ratio,
            "symbol": ticker
        }
        res = db.averages.update({"time": end},
            new_doc,
            upsert=True)
        msg = f"Moving Average: {ratio} recorded at {end}"
        if res["updatedExisting"]:
            msg += ", overwrote existing"
        print(msg)

    def calc_avg(self, start, end, ticker="SPY"):
        agg_query = [
                {"$match": {"timestamp": {"$gte": start, "$lt": end}}},
                {"$match": {"symbols": ticker}},
                {"$facet": {
                    "Bears": [
                        {"$match": {"label": "Bearish"}},
                        {"$count": "count"}
                        ],
                    "Bulls":[
                        {"$match": {"label": "Bullish"}},
                        {"$count": "count"}
                    ],
                    "PredBears":[
                        {"$match": {"label": ""}},
                        {"$match": {"prediction": "Bearish"}},
                        {"$count": "count"}
                    ],
                    "PredBulls":[
                        {"$match": {"label": ""}},
                        {"$match": {"prediction": "Bullish"}},
                        {"$count": "count"}
                    ]}
                },
                { "$project": {
                    "ratio": {"$divide": [
                        {"$sum": [
                            {"$arrayElemAt": ["$Bulls.count", 0]},
                            {"$arrayElemAt": ["$PredBulls.count", 0]}
                        ]}, 
                        {"$sum": [
                            {"$arrayElemAt": ["$Bulls.count", 0]},
                            {"$arrayElemAt": ["$PredBulls.count", 0]},
                            {"$arrayElemAt": ["$PredBears.count", 0]}, 
                            {"$arrayElemAt": ["$Bears.count", 0]},
                            0.001]}
                    ]}
                }}
            ]
        result = db.twits.aggregate(agg_query)
        return list(result)[0]["ratio"]
    
    def run(self):
        while True:
            self.calc_now()
            sleep(self.increments*60)
"""
Does the moving average calculation
"""
from database import get_db
from datetime import datetime, timedelta
from time import sleep
from utils import get_loggers

class Avg_calc:
    def __init__(self, window=30, increments=2):
        self.window = timedelta(minutes=window)
        self.increments = increments
        self.logger = get_loggers(__name__, "logs/data.log")
        self.db = get_db()

    def calc_now(self, ticker="SPY"):
        t =  self.round_time(datetime.utcnow())
        self.update(t, ticker)

    def calc_past(self, ticker="SPY"):
        latest = list(self.db.averages.find().sort("time", -1).limit(1))[0]["time"]
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
        res = self.db.averages.update({"time": end},
            new_doc,
            upsert=True)
        msg = f"Moving Average: {ratio} recorded at {end}"
        if res["updatedExisting"]:
            msg += ", overwrote existing"
        self.logger.info(msg)

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
        result = self.db.twits.aggregate(agg_query)
        return list(result)[0]["ratio"]
    
    def run(self):
        while True:
            self.calc_now()
            sleep(self.increments*60)

if __name__ == "__main__":
    Avg_calc().run()
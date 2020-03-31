"""
Does the moving average calculation
"""
from datetime import datetime, timedelta
from time import sleep
from utils.logging import get_loggers
from utils.database import get_db, config
from itertools import cycle
class Avg_calc:
    def __init__(self, tickers, window=30, increments=2):
        """
        increments must be a factor of 60, so that it can 
        split an hour into equal slots.
        """
        self.window = timedelta(minutes=window)
        self.increments = increments
        self.logger = get_loggers(__name__, "logs/data.log")
        self.db = get_db()
        self.tickers = config["tickers"]

    def calc_now(self, ticker="SPY"):
        """
        calculates the average for the ticker for the currect time.
        Takes all the twits in the window time frame, and records in 
        database
        """
        t =  self.round_time(datetime.utcnow())
        self.update(t, ticker)

    def calc_past(self, start=None, ticker="SPY"):
        """
        calculates all averages from the start time to now of the given
        ticker. If start is None, it is set to be the lastest average
        found in storage
        """
        collection = self.db.get_collection(f"averages.{ticker}")
        if start is None:
            start = list(collection.find().sort("time", -1).limit(1))[0]["time"]
            start += self.increments

        while start <= self.round_time(datetime.utcnow()):
            self.update(start, ticker)
            start += self.increments
    
    def round_time(self, dt):
        """
        rounds the time to the nearest time increment.
        Ex: if increment is 2 minutes, it will round the time
            to the nearest product of 2.
        """
        if dt.second >= 30:
            dt = dt + timedelta(minutes=1)
        dt = dt.replace(second=0, microsecond=0)
        if dt.minute%self.increments:
            dt = dt.replace(minute=dt.minute//self.increments)
        return dt

    def update(self, time, ticker="SPY"):
        """
        calculates and updates the average between time - window and time
        of the ticker.
        """
        collection = self.db.get_collection(f"averages.{ticker}")
        end = time
        start = time - self.window
        ratio = self.calc_avg(start, end, ticker)
        new_doc = {
            "time": end,
            "MovingAvg": ratio
        }
        res = collection.update({"time": end},
                                {"$set": new_doc},
                                upsert=True)
        msg = f"Moving Average: {ratio:.3f} for ${ticker} recorded at {end:%Y-%m-%d %H:%M} UTC"
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
            for ticker in self.tickers:
                self.calc_now(ticker)
            sleep(self.increments*60)

if __name__ == "__main__":
    Avg_calc(config["tickers"]).run()
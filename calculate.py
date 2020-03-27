"""
Does the moving average calculation
"""
from database import db
from datetime import datetime, timedelta
from time import sleep
class Calculator(object):
    def __init__(self, offset=15, ema_cost=0.9):
        self.db = db
        self.collection = self.db.averages
        self.offset = timedelta(minutes=offset)
        self.multiplier = 0.95
        
    def update(self):
        latest = self.collection.find_one_and_update(
                    {"latest": True},
                    {"$set": {"latest": False}})
        if latest is None:
            latest = {
                "start": datetime.min,
                "end": datetime.utcnow() - self.offset,
                "ema": self.compute_ratio(datetime.min, end=datetime.utcnow() - self.offset),
                "latest": False
            }
            self.collection.insert_one(latest)

        next_end = latest["end"]
        old_ema = latest["ema"]
        while next_end < (datetime.utcnow()-self.offset*2):
            ema = self.compute_ratio(next_end, offset=self.offset)
            ema = self.exp_moving_avg(ema, old_ema)
            self.insert_point(ema, next_end, next_end+self.offset, latest=False)
            next_end = next_end + self.offset
            old_ema = ema

        close = self.compute_ratio(next_end, offset=self.offset)
        close = self.exp_moving_avg(close, old_ema)
        self.insert_point(close, next_end, next_end+self.offset)

    def insert_point(self, ema, start, end, latest=True):
        new_point = {
            "latest": latest,
            "start": start,
            "end": end,
            "ema": ema
        }
        self.collection.insert_one(new_point)
        print(f"EMA: {ema} at {end}")

    def exp_moving_avg(self, new, old):
        return (new - old)*self.multiplier + old
    
    def compute_ratio(self, start, end=None, offset=None, ticker="SPY"):
        """
        computes the ratio of bullish to bearish of all twits 
        from the start time plus offset time
        """
        if end is None and offset is None:
            raise ValueError("must specify end datetime or offset time")
        if end is None:
            end = start + offset
        bullish = self.db.twits.count_documents({
                    "symbols": ticker,
                    "timestamp": {"$gte": start, "$lt": end},
                    "label": {"$eq": "Bullish"}
                    })
        bearish = self.db.twits.count_documents({
                    "symbols": ticker,
                    "timestamp": {"$gte": start, "$lt": end},
                    "label": {"$eq": "Bearish"}
                    })
        return bullish/(bullish+bearish+0.0001)

    def run(self, wait=10):
        while True:
            self.update()
            sleep(wait*60)

if __name__ == "__main__":
    Calculator().run()
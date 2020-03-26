"""
Does the moving average calculation
"""
from database import db
from datetime import datetime, timedelta
class Calculator(object):
    def __init__(self, offset=10, ema_cost=0.9):
        self.db = db
        self.collection = self.db.averages
        self.offset = timedelta(minutes=offset)
        self.multiplier = 0.9
        
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
            
        close = self.compute_ratio(latest["end"], offset=self.offset)

        new_ratio = {
            "latest": True,
            "start": latest["end"],
            "end": latest["end"] + self.offset,
            "ema": self.exp_moving_avg(close, latest["ema"])
        }
        self.collection.insert_one(new_ratio)
        
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
        bullish = self.db.twits.count({
                    "symbols": ticker,
                    "timestamp": {"$gte": start, "$lt": end},
                    "label": {"$eq": "Bullish"}
                    })
        bearish = self.db.twits.count({
                    "symbols": ticker,
                    "timestamp": {"$gte": start, "$lt": end},
                    "label": {"$eq": "Bearish"}
                    })
        return bullish/(bullish+bearish)
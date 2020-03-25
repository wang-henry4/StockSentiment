import requests
import json
import os
from pymongo import MongoClient
from time import sleep
from database import db

class ST_crawler:
    def __init__ (self):
        self.url = "https://api.stocktwits.com/api/2/streams/symbol/{}.json"
        self.db = db
        self.targetDates = "consider a range of time for the future"

    def get_tweets(self, ticker):
        """
        calls the api for twits and adds them to the mongodb database
        checks the twit id to make sure it is new.
        """
        req_url = self.url.format(ticker)
        try:
            response = requests.get(req_url)
        except:
            print("get request error!")

        try:
            data = json.loads(response.text)
        except:
            print("json decode error!")
    
        if data and data["response"]["status"] == 200:
            twits = []
            for s in data["messages"]:
                if self.db.twits.find_one({"_id": s["id"]}):
                    # twit already exists
                    continue
                # each individual message dict --- s is a dict=
                text = s["body"]
                text = text.replace("\n", " ").strip()
                label = s["entities"]["sentiment"]["basic"] if s["entities"]["sentiment"] else ""
                twit = {
                    "_id": s["id"],
                    "body": text,
                    "timestamp": s["created_at"],
                    "label": label,
                    "symbols": [sym["symbol"] for sym in s["symbols"]]
                }
                
                twits.append(twit)
            if twits:
                self.db.twits.insert_many(twits)
                print(f"inserted {len(twits)} twits")
        elif data["responce"]["status"] == 429:
            raise Exception("Rate Limit Exceeded")
        else:
            print("bad json response")

    def crawl(self, ticker, wait=18):
        while True:
            self.get_tweets(ticker)
            sleep(wait)


if __name__ == "__main__":
    app = ST_crawler()
    app.crawl("msft")
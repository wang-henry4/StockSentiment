import requests
import json
import os
from pymongo import MongoClient
from time import sleep

class ST_crawler:
    def __init__ (self, db_url="mongodb://127.0.0.1:27017/?compressors=disabled&gssapiServiceName=mongodb"):
        self.url = "https://api.stocktwits.com/api/2/streams/symbol/{}.json"
        self.client = MongoClient(db_url)
        self.db = self.client.twits
        self.targetDates = "consider a range of time for the future"

    def get_tweets(self, ticker):
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
                    "label": label
                }
                
                twits.append(twit)
            if twits:
                self.db.twits.insert_many(twits)
                print(f"inserted {len(twits)} twits")
        elif data["responce"]["status"] == 429:
            raise Exception("Rate Limit Exceeded")
        else:
            print("bad json response")

if __name__ == "__main__":
    app = ST_crawler()
    while True: 
        app.get_tweets("msft")
        sleep(18)
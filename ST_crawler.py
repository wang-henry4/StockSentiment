import requests
import json
import os
import datetime
from pymongo import MongoClient
from time import sleep
from database import db, config
from transformers import pipeline

class ST_crawler:
    def __init__ (self):
        self.url = "https://api.stocktwits.com/api/2/streams/symbol/{}.json"
        self.db = db
        self.collection = self.db.twits
        self.targetDates = "consider a range of time for the future"
        self.nlp = pipeline("sentiment-analysis")

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
            print(response.text)
    
        if data and data["response"]["status"] == 200:
            twits = []
            texts = []
            for s in data["messages"]:
                if self.db.twits.find_one({"_id": s["id"]}):
                    # twit already exists
                    continue
                # each individual message dict --- s is a dict=
                text = s["body"]
                text = text.replace("\n", " ").strip()
                texts.append(text)
                label = s["entities"]["sentiment"]["basic"] if s["entities"]["sentiment"] else ""
                
                pred_label, prob = self.apply_nlp(text)
                twit = {
                    "_id": s["id"],
                    "body": text,
                    "timestamp": self.convert_date(s["created_at"]),
                    "label": label,
                    "symbols": [sym["symbol"] for sym in s["symbols"]],
                    "prediction": pred_label,
                    "probability": prob
                }
                twits.append(twit)

            if twits:
                self.collection.insert_many(twits)
                print(f"inserted {len(twits)} twits")
        elif data["responce"]["status"] == 429:
            raise Exception("Rate Limit Exceeded")
        else:
            print("bad json response")

    def apply_nlp(self, text):
        prediction = list(self.nlp(text))[0]
        label = prediction["label"]
        probability = float(prediction["score"])
        if label == "POSITIVE":
            label = "Bullish"
        else:
            label = "Bearish"
        return label, probability

    def convert_date(self, date_string):
        date_string = date_string[:-1]
        date, time = date_string.split("T")
        date = date.split("-")
        time = time.split(":")
        dt =[int(num) for num in date + time]
        return datetime.datetime(*dt)

    def crawl(self, ticker, wait=18):
        while True:
            self.get_tweets(ticker)
            sleep(wait)

if __name__ == "__main__":
    app = ST_crawler()
    app.crawl(config["ticker"])
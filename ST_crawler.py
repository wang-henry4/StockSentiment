import requests
import json
import os
from datetime import datetime
from utils.logging import get_loggers
from pymongo import MongoClient
from time import sleep
from utils.database import get_db, config
from transformers import pipeline
from itertools import cycle
class ST_crawler:
    def __init__ (self, tickers, img_dir=None):
        self.url = "https://api.stocktwits.com/api/2/streams/symbol/{}.json"
        self.db = get_db()

        # DB collection
        self.collection = self.db.twits
        
        #BERT pipeline
        self.nlp = pipeline("sentiment-analysis")
        
        #Ticker generator
        self.tickers = cycle(tickers)
        
        # Logger object
        self.logger = get_loggers(__name__, "logs/crawler.log")

        self.img_dir = img_dir

    def get_tweets(self, ticker):
        """
        calls the api for twits and adds them to the mongodb database
        checks the twit id to make sure it is new.
        """
        req_url = self.url.format(ticker)
        try:
            response = requests.get(req_url)
        except:
            self.logger.error(f"get request error: {response} \n time {datetime.utcnow()}")
            return

        try:
            data = json.loads(response.text)
        except:
            self.logger.error(f"json decode error: {response.text} \n time {datetime.utcnow()}")
            return

        if data and data["response"]["status"] == 200:
            twits = []

            for s in data["messages"]:
                if self.db.twits.find_one({"_id": s["id"]}):
                    # twit already exists
                    continue
                # each individual message dict --- s is a dict=
                twits.append(self.process_message(s))
                
            if twits:
                self.collection.insert_many(twits)
                self.logger.info(f"inserted {len(twits)} twits for ${ticker}")

        elif data["responce"]["status"] == 429:
            self.logger.warning("request limit exceeded")
        else:
            self.logger.error("bad json response")

    def process_message(self, msg):
        """
        processes a single twit json and returns the doc to be saved
        """
        text = msg["body"]
        text = text.replace("\n", " ").strip()
        label = msg["entities"]["sentiment"]["basic"] if msg["entities"]["sentiment"] else ""
        imgurl = ""
        if "chart" in msg["entities"]:
            imgurl = msg["entities"]["chart"]["large"]
            self.save_img(imgurl, msg["id"])
        imgflag = (imgurl != "")
        
        pred_label, prob = self.apply_nlp(text)
        prob = "{:.4f}".format(prob)
        #print(prob)
        twit = {
            "_id": msg["id"],
            "body": text,
            "timestamp": self.convert_date(msg["created_at"]),
            "label": label,
            "symbols": [sym["symbol"] for sym in msg["symbols"]],
            "prediction": pred_label,
            "probability": prob,
            "imgflag" : imgflag,
            "imgurl" : imgurl
        }
        return twit

    def save_img(self, img_url, uid):
        """
        Given an image url, and unique id of twit,
        saves the image with the uid as the name.
        If url is empty or is a gif then it does nothing.
        """
        if self.img_dir is None:
            return "no directory specified for images"

        if not img_url or img_url[-3:] == "gif":
            return "url empty or is gif"

        response = requests.get(img_url)
        if response.status_code == 200:

            name = os.path.join(self.img_dir, str(uid) + ".png")
            with open(name, "wb") as file:
                file.write(response.content)
            return "Write success"

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
        return datetime(*dt)

    def crawl(self, wait=18):
        while True:
            ticker = next(self.tickers)
            self.get_tweets(ticker)
            sleep(wait)

if __name__ == "__main__":
    app = ST_crawler(config["tickers"], config["img_dir"])
    app.crawl()
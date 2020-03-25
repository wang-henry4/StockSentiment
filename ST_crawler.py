# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 18:02:56 2020

@author: Tang
"""

import requests
import json
import os


class ST_crawler:
    def __init__ (self):
        self.url = "https://api.stocktwits.com/api/2/streams/symbol/{}.json"
        self.tweets = []
        self.labels = []
        self.targetDates = "consider a range of time for the future"

        if not os.path.isdir("stocks"):
            os.mkdir("stocks")
    
    def get_tweets(self,ticker):
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
            for s in data["messages"]:
                # each individual message dict --- s is a dict=
                text = s["body"]
                text = text.replace("\n", " ").strip()
                label = s["entities"]["sentiment"]["basic"] if s["entities"]["sentiment"] else ""
                self.tweets.append(text)
                self.labels.append(label)
        else:
            print("bad json response")

    def tweets_get_write(self, symbol):
        self.get_tweets(symbol)
        tw_fName = "stocks/" + symbol + "_tweet.txt"
        lb_fName = "stocks/" + symbol + "_label.txt"
        with open(tw_fName, "w",encoding='utf-8') as f:
            f.write('\n'.join(self.tweets))
        with open(lb_fName, "w",encoding='utf-8') as f:
            f.write('\n'.join(self.labels))
    
app = ST_crawler()
app.tweets_get_write("msft")

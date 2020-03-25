"""
Does the moving average calculation
"""
from pymongo import MongoClient
from database import db

class Calculator:
    def __init__(self):
        self.db = db
        self.collection = self.db.averages
    
    def update(self):
        pass

from flask import Flask
from flask_restful import Resource, Api
from utils.database import get_db


app = Flask(__name__)
api = Api(app)
db = get_db()

class Averages(Resource):
    def get(self, ticker):
        collection = db.get_collection(f"averages.{ticker}")
        result = collection.find().sort("time", -1).limit(1)[0]
        return {"time": str(result["time"]), 
                "avg": str(result["MovingAvg"])}


api.add_resource(Averages, '/averages/<string:ticker>')

if __name__ == '__main__':
    app.run(debug=False, host="localhost")
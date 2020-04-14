from flask import Flask
from flask_restful import Resource, Api
from utils.database import get_db



app = Flask(__name__)
api = Api(app)
db = get_db()


class Averages(Resource):
    def get(self, ticker):
        collection = db.get_collection(f"averages.{ticker}")
        collection.find_one
        return {'hello': 'world'}





api.add_resource(Averages, '/')

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request
from flask_cors import CORS
from influxdb import processTestData
import logging

api = Flask(__name__)
CORS(api)
logging.basicConfig(filename='history.log', level=logging.INFO)

@api.route('/baseline', methods=['GET'])
def processData():
  processTestData(request.args.get('testId'), request.args.get('status'), request.args.get('rfc'))
  return "Done"

@api.route('/', methods=['GET'])
def health():
  return "Hello!"

if __name__ == '__main__':
    api.run(host='0.0.0.0') 
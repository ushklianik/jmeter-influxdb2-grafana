from flask import Flask, request, make_response
from flask_cors import CORS
from influxdb import deleteTestData, deleteTestPoint, addOrUpdateTest, connectToInfluxDB, closeInfluxdbConnection
from report import generateReport
from login import checkAccess
import logging
import json

api = Flask(__name__)
CORS(api)
logging.basicConfig(filename='history.log', level=logging.INFO)

config = open('./config/config.json')
config = json.load(config) 
grafana_server = config["grafana"]["grafana_server"]  

def processTestData(runId, status, testName, user, baseline_runId = None, build = None):
  if(checkAccess(user)):
    connectToInfluxDB()
    if(runId != '' and status != ''):
      if(status == 'DeleteTest'):
        try:
          deleteTestData(runId)
        except Exception as er:
          logging.warning(er)
      elif(status == 'DeleteTestStatus'):
        try:
          deleteTestPoint(runId)
        except Exception as er:
          logging.warning(er)
      elif(status == 'createReport'):
        try:
          generateReport(runId, testName, baseline_runId)
        except Exception as er:
          logging.warning(er)
      elif(status == 'Baseline'):
        try:
          addOrUpdateTest(runId, status, build, testName)
        except Exception as er:
          logging.warning(er)
    closeInfluxdbConnection()

@api.route('/baseline', methods=['GET'])
def processData():
  processTestData(runId = request.args.get('runId'), status = request.args.get('status'), build = request.args.get('build'), testName = request.args.get('testName'), user = request.args.get('user'))
  resp = make_response("Done")
  resp.headers['Access-Control-Allow-Origin'] = grafana_server
  resp.headers['access-control-allow-methods'] = '*'
  resp.headers['access-control-allow-credentials'] = 'true'
  return resp

@api.route('/', methods=['GET'])
def health():
  resp = make_response("Hello! I am active")
  resp.headers['Access-Control-Allow-Origin'] = grafana_server
  resp.headers['access-control-allow-methods'] = '*'
  resp.headers['access-control-allow-credentials'] = 'true'
  return resp

@api.route('/report', methods=['GET'])
def createReport():
  processTestData(runId = request.args.get('current_runId'), status = "createReport", testName = request.args.get('testName'), user = request.args.get('user'), baseline_runId = request.args.get('baseline_runId'))
  resp = make_response("Done")
  resp.headers['Access-Control-Allow-Origin'] = grafana_server
  resp.headers['access-control-allow-methods'] = '*'
  resp.headers['access-control-allow-credentials'] = 'true'
  return resp

if __name__ == '__main__':
    api.run(host='0.0.0.0', port=5000) 
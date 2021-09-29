from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

bucket = "jmeter"
token = "token"
source_mes = "samples"
target_mes = "tests"
org = "PMI"
url = "http://your_ip:8086"


client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()
delete_api = client.delete_api()


def processTestData(testId, status, rfc):
    if(testId != '' and status != ''):
        if(status == 'DeleteTest'):
            try:
                deleteTestData(testId)
            except er:
                print(er)
        if(status == 'DeleteTestStatus'):
            try:
                deleteTestPoint(testId)
            except er:
                print(er)
        else:
            try:
                addOrUpdateTest(testId, status, rfc)
            except er:
                print(er)

def addBaseline(testId, status, rfc):
    start_time = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                            '|> range(start: -1y)' +
                                            '|> filter(fn: (r) => r["_measurement"] == "'+source_mes+'")' +
                                            '|> filter(fn: (r) => r["_field"] == "duration")' +
                                            '|> filter(fn: (r) => r["testId"] == "'+testId+'")' +
                                            '|> keep(columns: ["_time"])' +
                                            '|> min(column: "_time")' +
                                            '|> rename(columns: {_time: "startTime"})', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                        date_time_format="RFC3339"))
    for row in start_time:
        if not len(row) == 0:
            start_time = row[3]
            start_time = int(datetime.strptime(start_time[0:19], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000)

    avg_tr = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+source_mes+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "duration")' +
                                    '|> filter(fn: (r) => r["testId"] == "'+testId+'")' +
                                    '|> filter(fn: (r) => r["sample_type"] == "transaction")' +
                                    '|> keep(columns: ["_value"])' +
                                    '|> mean()', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
    for row in avg_tr:
        if not len(row) == 0:
            avg_tr = row[3]
    
    median_tr = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+source_mes+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "duration")' +
                                    '|> filter(fn: (r) => r["testId"] == "'+testId+'")' +
                                    '|> filter(fn: (r) => r["sample_type"] == "transaction")' +
                                    '|> keep(columns: ["_value"])' +
                                    '|> median()', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
    for row in median_tr:
        if not len(row) == 0:
            median_tr = row[3]
    
    end_time = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+source_mes+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "duration")' +
                                    '|> filter(fn: (r) => r["testId"] == "'+testId+'")' +
                                    '|> keep(columns: ["_time"])' +
                                    '|> max(column: "_time")' +
                                    '|> rename(columns: {_time: "startTime"})', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
    for row in end_time:
        if not len(row) == 0:
            end_time = row[3]
            end_time = int(datetime.strptime(end_time[0:19], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000)

    p = Point("tests").tag("testId", testId).tag("startTime", start_time).tag("endTime", end_time).tag("testProfile", testId[14:]).tag("status", status).tag("rfc", rfc).field("median_tr", median_tr).field("avg_tr", avg_tr)
    write_api.write(bucket=bucket, record=p)

def addOrUpdateTest(testId, status, rfc):
    isTestExist = False
    tests = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                 '|> range(start: -1y)' +
                                 '|> filter(fn: (r) => r["_measurement"] == "'+target_mes+'")' +
                                 '|> filter(fn: (r) => r["_field"] == "status")' +
                                 '|> filter(fn: (r) => r["testId"] == "'+testId+'")' +
                                 '|> group(columns: ["testId"])' +
                                 '|> count()' +
                                 '|> keep(columns: ["testId"])', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                             date_time_format="RFC3339"))
    for row in tests:
        if not len(row) == 0:
            isTestExist = True
    if(isTestExist):
        deleteTestPoint(testId)
        addBaseline(testId, status, rfc)
    else:
        addBaseline(testId, status, rfc)

def deleteTestPoint(testId):
    start = "2019-01-01T00:00:00Z"
    stop = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    delete_api.delete(start, stop, '_measurement="'+target_mes+'" AND testId="'+testId+'"',bucket=bucket, org=org)

def deleteTestData(testId):
    start = "2019-01-01T00:00:00Z"
    stop = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    delete_api.delete(start, stop, '_measurement="'+source_mes+'" AND testId="'+testId+'"',bucket=bucket, org=org)
    delete_api.delete(start, stop, '_measurement="'+target_mes+'" AND testId="'+testId+'"',bucket=bucket, org=org)
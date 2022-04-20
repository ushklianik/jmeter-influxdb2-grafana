from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
import logging
import json

try:
    config = open('./config/config.json')
    config = json.load(config)   
    bucket = config["influxdb"]["bucket"]
    org = config["influxdb"]["org"]
    jmeter_metrics_measurement = config["influxdb"]["jmeter_metrics_measurement"]
    jmeter_stats_measurement = config["influxdb"]["jmeter_stats_measurement"]
    jmeter_field = config["influxdb"]["jmeter_field"]
except Exception as er:
    logging.warning('ERROR: check your config files')
    logging.warning(er)

def connectToInfluxDB():
    try:
        global influxdbClient
        influxdbClient = InfluxDBClient.from_config_file("./config/influxdb.ini")
        global write_api
        write_api = influxdbClient.write_api(write_options=SYNCHRONOUS)
        global query_api
        query_api = influxdbClient.query_api()
        global delete_api
        delete_api = influxdbClient.delete_api()
    except Exception as er:
        logging.warning('ERROR: connection to influxdb failed')
        logging.warning(er)

def closeInfluxdbConnection():
    try:
        global influxdbClient
        influxdbClient.close()
    except Exception as er:
        logging.warning('ERROR: influxdb connection closing failed')
        logging.warning(er)


def addBaseline(runId, status, build, testName):
    start_time = getTestStartTime(runId)
    end_time = getTestEndTime(runId)
    avg_tr = getAverageTransactionTime(runId)
    median_tr = getMedianTransactionTime(runId)
    testType = getTestType(runId)
    percentile_tr = getPercentileTransactionTime(runId)
    try:
        p = Point("tests").tag("runId", runId) \
            .tag("startTime", start_time).tag("endTime", end_time) \
            .tag("testName", testName).tag("status", status) \
            .tag("build", build) \
            .tag("testType", testType) \
            .field("median_tr", median_tr) \
            .field("avg_tr", avg_tr) \
            .field("percentile_tr", percentile_tr)
        write_api.write(bucket=bucket, record=p)
    except Exception as er:
        logging.warning('ERROR: baseline stats uploading failed')
        logging.warning(er)


def addOrUpdateTest(runId, status, build, testName):
    isTestExist = False
    tests = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                 '|> range(start: -1y)' +
                                 '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_stats_measurement+'")' +
                                 '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                 '|> group(columns: ["runId"])' +
                                 '|> count()' +
                                 '|> keep(columns: ["runId"])', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                             date_time_format="RFC3339"))
    for row in tests:
        if not len(row) == 0:
            isTestExist = True
    if(isTestExist):
        deleteTestPoint(runId)
        addBaseline(runId, status, build, testName)
    else:
        addBaseline(runId, status, build, testName)

def deleteTestPoint(runId):
    start = "2019-01-01T00:00:00Z"
    stop = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        delete_api.delete(start, stop, '_measurement="'+jmeter_stats_measurement+'" AND runId="'+runId+'"',bucket=bucket, org=org)
    except Exception as er:
        logging.warning('ERROR: deleteTestPoint method failed')
        logging.warning(er)

def deleteTestData(runId):
    start = "2019-01-01T00:00:00Z"
    stop = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        delete_api.delete(start, stop, '_measurement="'+jmeter_metrics_measurement+'" AND runId="'+runId+'"',bucket=bucket, org=org)
        delete_api.delete(start, stop, '_measurement="'+jmeter_stats_measurement+'" AND runId="'+runId+'"',bucket=bucket, org=org)
        delete_api.delete(start, stop, '_measurement="virtualUsers" AND runId="'+runId+'"',bucket=bucket, org=org)
    except Exception as er:
        logging.warning('ERROR: deleteTestData method failed')
        logging.warning(er)
    

def getTestStartTime(runId):
    start_time = "Start time not found"
    try:
        start_time = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> keep(columns: ["_time"])' +
                                    '|> min(column: "_time")' +
                                    '|> rename(columns: {_time: "startTime"})', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[], date_time_format="RFC3339"))
        for row in start_time:
            if not len(row) == 0:
                start_time = row[3]
                start_time = int(datetime.datetime.strptime(start_time[0:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
    except Exception as er:
        logging.warning('ERROR: getTestStartTime method failed')
        logging.warning(er)
    return start_time

def getTestType(runId):
    testType = "Test type not found"
    try:
        testType = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> keep(columns: ["testType"])' +
                                    '|> first(column: "testType")', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[], date_time_format="RFC3339"))
        for row in testType:
            if not len(row) == 0:
                testType = row[3]
    except Exception as er:
        logging.warning('ERROR: getTestStartTime method failed')
        logging.warning(er)
    return testType

def getTestEndTime(runId):
    end_time = "End time not found"
    try:
        end_time = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> keep(columns: ["_time"])' +
                                    '|> max(column: "_time")' +
                                    '|> rename(columns: {_time: "startTime"})', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[], date_time_format="RFC3339"))
        for row in end_time:
            if not len(row) == 0:
                end_time = row[3]
                end_time = int(datetime.datetime.strptime(end_time[0:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
    except Exception as er:
        logging.warning('ERROR: getTestEndTime method failed')
        logging.warning(er)        
    return end_time

def getMaxThreads(runId):
    max_threads = "Max threads not found"
    try:
        max_threads = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "virtualUsers")' +
                                    '|> filter(fn: (r) => r["_field"] == "maxActiveThreads")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> keep(columns: ["_value"])' +
                                    '|> max(column: "_value")', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[], date_time_format="RFC3339"))
        for row in max_threads:
            if not len(row) == 0:
                max_threads = row[3]
    except Exception as er:
        logging.warning('ERROR: getMaxThreads method failed')
        logging.warning(er)
    return max_threads

def getBaselineRunId(testName):
    baseline_runId = "Baseline test ID not found"
    try:
        baseline_runId = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_stats_measurement+'")' +
                                    '|> filter(fn: (r) => r["status"] == "Baseline")' +
                                    '|> filter(fn: (r) => r["_field"] == "avg_tr")' +
                                    '|> filter(fn: (r) => r["testName"] == "'+testName+'")' +
                                    '|> keep(columns: ["runId"])' +
                                    '|> group()' +
                                    '|> sort(columns: ["runId"], desc: true)' +
                                    '|> limit(n: 1)', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
        for row in baseline_runId:
            if not len(row) == 0:
                baseline_runId = row[3]
    except Exception as er:
        logging.warning('ERROR: getBaselineRunId method failed')
        logging.warning(er)
    return baseline_runId

def getLabelsCount(runId):
    labels_count = ""
    try:
        labels_count = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> filter(fn: (r) => r["sampleType"] == "transaction")' +
                                    '|> group()' +
                                    '|> keep(columns: ["requestName"])' +
                                    '|> distinct(column: "requestName")' +
                                    '|> count()', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
        for row in labels_count:
            if not len(row) == 0:
                labels_count = row[3]
    except Exception as er:
        logging.warning('ERROR: getLabelsCount method failed')
        logging.warning(er)
    return labels_count

def getAverageTransactionTime(runId):
    avg_tr = ""
    try:
        avg_tr = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                    '|> range(start: -1y)' +
                                    '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                    '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                    '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                    '|> filter(fn: (r) => r["sampleType"] == "transaction")' +
                                    '|> keep(columns: ["_value"])' +
                                    '|> mean()', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                date_time_format="RFC3339"))
        for row in avg_tr:
            if not len(row) == 0:
                avg_tr = row[3]
    except Exception as er:
        logging.warning('ERROR: getAverageTransactionTime method failed')
        logging.warning(er)
    return avg_tr

def getMedianTransactionTime(runId):
    median_tr = ""
    try:
        median_tr = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                        '|> range(start: -1y)' +
                                        '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                        '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                        '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                        '|> filter(fn: (r) => r["sampleType"] == "transaction")' +
                                        '|> keep(columns: ["_value"])' +
                                        '|> toFloat()' +
                                        '|> median()', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                    date_time_format="RFC3339"))
        for row in median_tr:
            if not len(row) == 0:
                median_tr = row[3]
    except Exception as er:
        logging.warning('ERROR: getMedianTransactionTime method failed')
        logging.warning(er)
    return median_tr

def getPercentileTransactionTime(runId):
    percentile_tr = ""
    try:
        percentile_tr = query_api.query_csv('from(bucket: "'+bucket+'")'+
                                        '|> range(start: -1y)' +
                                        '|> filter(fn: (r) => r["_measurement"] == "'+jmeter_metrics_measurement+'")' +
                                        '|> filter(fn: (r) => r["_field"] == "'+jmeter_field+'")' +
                                        '|> filter(fn: (r) => r["runId"] == "'+runId+'")' +
                                        '|> filter(fn: (r) => r["sampleType"] == "transaction")' +
                                        '|> keep(columns: ["_value"])' +
                                        '|> toFloat()' +
                                        '|> quantile(q: 0.90)', dialect=Dialect(header=False, delimiter=",", comment_prefix="#", annotations=[],
                                                                                                    date_time_format="RFC3339"))
        for row in percentile_tr:
            if not len(row) == 0:
                percentile_tr = row[3]
    except Exception as er:
        logging.warning('ERROR: getPercentileTransactionTime method failed')
        logging.warning(er)
    return percentile_tr
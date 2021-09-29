# About repo
This repository contains everything you need to visualize and analyze the results of JMeter testing.

- *backend-listener* folder contains custom backend listener to send metrics to influxdb 2.0.
- *grafana-dashboards* folder contains 3 grafana dashboards for different purposes.
- *flask-grafana-buttons* folder contains python code of Flask server to make grafana buttons responsive.

# Requirements
- JMeter 5.4.1^
- InfluxDB 2.0^
- Grafana 8.1.2^

# First things first: JMeter
First you need to put the backend-listener plugin to JMeter /lib/ext/ folder.

I would also recommend updating the following timeout configuration in the properties file:

```
#Influxdb timeouts
backend_influxdb.connection_timeout=3000
backend_influxdb.socket_timeout=5000
backend_influxdb.connection_request_timeout=1000
```

# Grafana dashboards
When importing dashboards, do not change the uid, this will break the connection between the dashboards.

## Requirements
- Button Panel plugin.

## Main dashboard
The main dashboard contains 2 tables: the test log, which displays each test and creates a link to a separate dashboard with test results.
And a baseline table that represents only the baselines for each test profile.

![image](https://user-images.githubusercontent.com/76432241/135265504-dbee2603-e5cc-47bb-ad3e-c40136cb1d56.png)

## JMeter test results
This dashboard visualizes all JMeter metrics.
At the top of the dashboard you can choose:
- testProfile: application name
- Test Id of the test
- Sample Type. In jmeter terminology, there are transactions and requests. For example, when you log in to the application, you perform one action or one transaction, but the browser sends several http requests to the server. Thus, a transaction is one logical action, requests are all http requests.
- Aggregation level: granularity of the graphs
- RFC is used when you mark test results as a baseline
Also on the dashboard you can find:
-stats
-response times
-throughput
-timeseries graphs and tables

![image](https://user-images.githubusercontent.com/76432241/135266292-fc6cbf5c-742b-4685-8ca6-f63f312281f9.png)

Also on top of the dashboards there are several buttons:
- You can mark the test results as a baseline. To do this, please enter the RFC number or leave it blank. Then click on the "Mark as a baseline" button.
After it, test will be displayed in Baseline table on main dashboard.
- You can mark the test as "Unacceptable".
- You can delete the test status, this means that the test will be without identifier (baseline or unacceptable).
- Or you can completely delete test results.

![image](https://user-images.githubusercontent.com/76432241/135266826-4790aa87-2d5e-43e6-8ecc-b28bda57f14e.png)

To make them responsive, please update the IP address of the Flask server in buttons configuration, more on this later.
![image](https://user-images.githubusercontent.com/76432241/135267025-a5361c11-b097-4c4b-a678-032830083b5e.png)

## JMeter Load Test Comparison

This dashboard is used to compare the current test results with the baseline.
After the test is completed:

- Choose testProfile
- Baseline Test Id (Note: you need to mark at least one test as a baseline so that you can compare the test results)
- Current Test Id
- Sample Type
- After you have selected all the necessary parameters, please wait a little, it will take some time to collect the metrics of both tests.
- Then you will be able to compare stats
- And Average and Median response times of both tests

![image](https://user-images.githubusercontent.com/76432241/135267848-a4c4c178-292b-457f-9a10-c6bd3d76c58e.png)


# Flask grafana server
It is used to make Grafana buttons responsive, can be installed on the same server as graphana or influxdb.

Libraries used:
- influxdb_client
- flask
- flask_cors
- logging

Note: Don't forget to update Influxdb2 configuarion like url and token.

To start the server, run start.py file, it will launch the server on port 5000 and will listen for requests from the grafana buutons and make requests to influxdb.



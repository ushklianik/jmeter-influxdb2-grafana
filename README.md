# About repo
This repository contains everything you need to visualize and analyze the results of JMeter testing.
- Grafana dashboards that allow you to manage test data in influxdb and compare different tests.
- Python service that makes buttons clickable in Grafana and allows you to create reports in the Azure wiki.

Now about the structure:
- *backend-listener* folder contains custom backend listener to send metrics to influxdb 2.
- *grafana-dashboards* folder contains 3 grafana dashboards for different purposes.
- *flask-grafana-buttons* folder contains python code of Flask server to make grafana buttons responsive.

# Requirements
- JMeter 5.4.3^
- InfluxDB 2.0^
- Grafana 8.1.2^
- Java 11

# Backend listener
Note that grafana dashboards and the python service will only work with the provided JMeter backend listener. Other listeners can send JMeter data with different field/tag names, which will require you to modify the dashboards and python code.

The plugin sends the following metrics to InfluxDB:

- Response code
- Error message
- Response body of the failed requests (can be configured);
- Connect time
- Latency
- The response time
- Type of the sample: transaction/request (It is very easy to split JMeter metrics by sampler type without the need for special names and regular expressions)

# First things first: JMeter
First you need to put the backend-listener plugin to JMeter /lib/ext/ folder.

# Grafana dashboards
When importing dashboards, do not change the uid, this will break the connection between the dashboards.

## Grafana set-up
If you will use the provided docker compose file. Grafana with all plugins will be installed automatically. If you want to install it in some other way or use some existing Grafana. You need to make sure that the following plugins are installed:
- cloudspout-button-panel
- grafana-image-renderer

To install plugins manually, run the following command: grafana-cli plugins install grafana-image-renderer (example)

# How to install and setup
If you want to install all the components using the provided docker-compose file:
1) First you need to install Docker Engine according to one of these instructions: [Link](https://docs.docker.com/engine/install/)
2) The next step is to install Docker Compose: [Link](https://docs.docker.com/compose/install/)
3) Copy folder flaskPerf and docker-compose file on your server (Note that the docker compose file must be in the same location as the flaskPerf folder)
4) Go to the folder with docker-compose file
5) Run the followng comand: docker-compose up -d (It will automatically install all tools and plugins)

If you want to install only flask service using docker:
1) First you need to install Docker Engine according to one of these instructions: [Link](https://docs.docker.com/engine/install/)
2) The next step is to install Docker Compose: [Link](https://docs.docker.com/compose/install/)
3) Copy folder flaskPerf and docker-compose file which stores only flask service on your server (Note that the docker compose file must be in the same location as the flaskPerf folder)
4) Go to the folder with docker-compose file
5) Run the followng comand: docker-compose -f docker-compose-only-flask.yml up -d (It will automatically install all tools and plugins)

If you want to install flask service without docker:
1) Copy folder flaskPerf on your server
2) Install python (The service was developed using python 3.9)
3) Install all the necessary dependencies. Run command: pip3 install --upgrade pip -r requirements.txt
4) Start flask service: python ./start.py

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

![image](https://user-images.githubusercontent.com/76432241/135269362-4beb8cda-1419-42eb-97d2-45d0bf22879a.png)

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



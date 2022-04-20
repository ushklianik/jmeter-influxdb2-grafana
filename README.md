# About repo

![image](https://user-images.githubusercontent.com/76432241/164237618-f5590a05-e777-423d-ba48-27aa8c3e0baf.png)

This repository contains everything you need to visualize and analyze the results of JMeter testing.
- Grafana dashboards that allow you to manage test data in influxdb and compare different tests.
- Python service that makes buttons clickable in Grafana and allows you to create reports in the Azure wiki.

Now about the structure:
- *backendListener* folder contains custom backend listener to send metrics to influxdb 2.
- *grafanaDashboards* folder contains 3 grafana dashboards for different purposes.
- *flaskPerf* folder contains python code of Flask server to make grafana buttons responsive.

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

# How to get started
## JMeter configuration

1) First you need to put the [backend-listener plugin](/backendListener/jmeter-plugin-influxdb2-listener-1.5-all.jar) to JMeter /lib/ext/ folder.
2) Fill in all required fields:

![image](https://user-images.githubusercontent.com/76432241/164194303-ae734ffa-6cb8-443f-9c03-61732518d001.png)

## How to install and configure

### Installation

If you will use the provided docker compose file. Grafana with all plugins will be installed automatically. If you want to install it in some other way or use some existing Grafana. You need to make sure that the following plugins are installed:
- cloudspout-button-panel
- grafana-image-renderer

To install plugins manually, run the following command: grafana-cli plugins install grafana-image-renderer (example)

#### If you want to install all the components using the provided docker-compose file:
1) First you need to install Docker Engine according to one of these instructions: [Link](https://docs.docker.com/engine/install/)
2) The next step is to install Docker Compose: [Link](https://docs.docker.com/compose/install/)
3) Copy folder flaskPerf and docker-compose file on your server (Note that the docker compose file must be in the same location as the flaskPerf folder)
4) Go to the folder with docker-compose file
5) Run the followng comand: docker-compose up -d (It will automatically install all tools and plugins)

#### If you want to install only flask service using docker:
1) First you need to install Docker Engine according to one of these instructions: [Link](https://docs.docker.com/engine/install/)
2) The next step is to install Docker Compose: [Link](https://docs.docker.com/compose/install/)
3) Copy folder flaskPerf and docker-compose file which stores only flask service on your server (Note that the docker compose file must be in the same location as the flaskPerf folder)
4) Go to the folder with docker-compose file
5) Run the followng comand: docker-compose -f docker-compose-only-flask.yml up -d (It will automatically install all tools and plugins)

#### If you want to install flask service without docker:
1) Copy folder flaskPerf on your server
2) Install python (The service was developed using python 3.9)
3) Install all the necessary dependencies. Run command: pip3 install --upgrade pip -r requirements.txt
4) Start flask service: python ./start.py

### Configuration

1) When all components are installed and running. First you need to add influxdb as a data source in Gfafana. Note, Flux should be chosen as a query language.

![image](https://user-images.githubusercontent.com/76432241/164196478-f02974f9-d98b-4bc3-b96a-629604184f63.png)

2) Then you need to import dashboards into Grafana. When importing dashboards, do not change the uid, this will break the connection between the dashboards.

![image](https://user-images.githubusercontent.com/76432241/164203838-ce660d53-1939-4fd2-86f7-2e0394b8caa4.png)

3) Then update the flaskUrl variable, it should store a link to the Flask service. This variable is used in buttons. For example:

![image](https://user-images.githubusercontent.com/76432241/164203192-f1e847d8-51c6-49fa-a570-ed29a96b607a.png)

4) Then you need to update Flask configuration files. All config files are located in config folder.
  - config.json: Here you need to update your Influxdb and Grafana data. Azure is only used for automatic wiki reporting. This will be described later.
  
![image](https://user-images.githubusercontent.com/76432241/164204601-8801e221-bf1d-43d0-b528-1e292cf001b5.png)
 
  - influxdb.ini: Here you need to update your Influxdb data.

![image](https://user-images.githubusercontent.com/76432241/164205184-cec6bd54-36d2-410e-83f8-32938cb05b72.png)

  - users.csv: This file stores Grafana users who have access to the Flask service.

![image](https://user-images.githubusercontent.com/76432241/164205539-533cef17-8a15-4ed2-adfc-cee70125f911.png)

5) After updating the configuration files, restart the Flask service.
6) Now you can run tests and enjoy :)

# Grafana dashboards overview

### Main dashboard
The main dashboard contains 2 tables and trend bar charts: 
- Test log table: which displays each test and creates a link to a separate dashboard with test results and a link to a comparison panel for comparison with the baseline.
- Baselines table: represents latest baselines for each test name and test type.
- Trend bar charts allow you to see how the mean, median, and 90 percentile change from test to test.

![image](https://user-images.githubusercontent.com/76432241/164207036-eb084c9c-7984-4a07-9459-1cd752eecbe2.png)

### JMeter test results
This dashboard visualizes all JMeter metrics.
Also on top of the dashboards there are several buttons:
- You can mark the test results as a baseline. To do this, please enter the application build number or leave it blank. Then click on the "Mark as a baseline" button.
After it, test will be displayed in Baseline table on main dashboard.
- You can delete the test status, this means that the test will be without identifier (baseline).
- Or you can completely delete test results.

![image](https://user-images.githubusercontent.com/76432241/164211523-2a2d0191-d7ac-4746-a934-a77db73c8f99.png)

## JMeter Load Test Comparison

This dashboard is used to compare the current test results with the baseline.

![image](https://user-images.githubusercontent.com/76432241/164211605-a35db248-a839-4d78-9fc9-e4f3209227ab.png)

### How to find the test

It is very easy to find the required time range of the test. You just need to click on the generated link in the test log table and it will automatically redirect you to a dashboard with a predefined time range of your test.

![](/img/how-to-find-the-test.gif)

### How to mark a test as a baseline

Sometimes we need to mark a particular test as a baseline or save build id of the application under test. To do this, you need to enter the build id in the text field and click the "Mark as a baseline" button.

![](/img/how-to-make-baseline.gif)

### How to delete test status

In case you made a mistake while saving the baseline, you can easily delete this status and reset it again.

![](/img/how-to-delete-test-status.gif)

### How to delete test results from db

Sometimes we can conduct experimental or warm-up tests that we don't have to store in the database. In such cases, you can delete the test from influxdb by clicking on the "Delete test results" button.

![](/img/how-to-delete-test-results.gif)

### How to compare current test with baseline 

To compare the test results, first of all, you need to mark at least one baseline test. Then you can click on the "compare" link in the test log, it will redirect you to the comparison dashboard, automatically comparing the test results with the latest baseline.

![](/img/how-to-compare-from-main.gif)

You can also go to the comparison panel by clicking on the "Compare" button on the test results dashboard.

![](/img/how-to-compare-from-dash.gif)

# How to generate report in azure wiki

1) First you need to update the data for integration with azure in config.json file:

![image](https://user-images.githubusercontent.com/76432241/164239117-04e70f64-f88e-4894-9870-3ffc371082bc.png)

2) To get azure_personal_access_token:
    - open azure devops
    - Click on "User settings"
    - Click on "Personal Access Tokens"
    - Create token with read/write permissions to wiki

![image](https://user-images.githubusercontent.com/76432241/164239560-90d04a1d-565b-458a-8e7b-93aaeaebf6d9.png)

3) To get azure_wiki_organization_url copy it from url

![image](https://user-images.githubusercontent.com/76432241/164240848-90aeb313-4af1-4c1e-b69d-00402a717d5c.png)

4) azure_wiki_project it is your project name
5) azure_wiki_identifier = azure_wiki_project + '.wiki'
6) azure_wiki_path it is path to parent folder, where reports should be located
7) 

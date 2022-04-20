from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import requests
import base64
import json
import random
from influxdb import getBaselineRunId, getTestStartTime, getTestEndTime, getMaxThreads, getLabelsCount
import json
import logging

################## Get data from configs #####################

def defineConfigVariables():
    try:
        global config 
        config = open('./config/config.json')
        config = json.load(config)   

        # grafana
        global grafana_server
        grafana_server = config["grafana"]["grafana_server"]
        global grafana_token
        grafana_token = config["grafana"]["grafana_token"]
        global grafana_dashboard
        grafana_dashboard = config["grafana"]["grafana_dashboard"]
        global grafana_orgId
        grafana_orgId = config["grafana"]["grafana_orgId"]
        global headers_grafana
        headers_grafana = {
            'Authorization': 'Bearer ' + grafana_token
        }

        # azure wiki
        global azure_personal_access_token
        azure_personal_access_token = config["azure"]["azure_personal_access_token"]
        global azure_wiki_organization_url
        azure_wiki_organization_url = config["azure"]["azure_wiki_organization_url"]
        global azure_wiki_project
        azure_wiki_project = config["azure"]["azure_wiki_project"]
        global azure_wiki_identifier
        azure_wiki_identifier = config["azure"]["azure_wiki_identifier"]
        global azure_wiki_path
        azure_wiki_path = config["azure"]["azure_wiki_path"]
        global headers_azure_attachments
        headers_azure_attachments = {
            'Accept': 'application/json',
            'Authorization': 'Basic ' + str(base64.b64encode(bytes(':'+azure_personal_access_token, 'ascii')), 'ascii'),
            'Content-Type': 'application/octet-stream'
        }
        global headers_page
        headers_page = {
            'Accept': 'application/json',
            'Authorization': 'Basic ' + str(base64.b64encode(bytes(':'+azure_personal_access_token, 'ascii')), 'ascii')
        }
    except Exception as er:
        logging.warning('ERROR: check your config files')
        logging.warning(er)

################## Declaring methods #####################
def putImageToAzure(metric, image, name, metrics_source, jmeter_images, hardware_images):
    for i in range(3):
        try:
            response = requests.put(
            url=azure_wiki_organization_url + "/"+azure_wiki_project+"/_apis/wiki/wikis/"+azure_wiki_identifier+"/attachments?name="+name+"&api-version=6.0", headers=headers_azure_attachments,data=image)
        except Exception as er:
            logging.warning('ERROR: uploading image to azure failed')
            logging.warning(er)    
        if response.status_code != 201:
            name = str(random.randint(1,100)) + name
        elif response.status_code == 201:
            if "JMeter" in metrics_source:
                jmeter_images[metric] = name
            elif "Hardware" in metrics_source:
                hardware_images[metric] = name
            break  

def downloadScreenshot(metric, dash_id, tmp_start, tmp_end, current_runId, testName, panelId, filename, width, height, metrics_source, jmeter_images, hardware_images, baseline_runId = None): 
    # The length of the median response time comparison table is calculated here, this value depends on the number of transactions
    if metric == "Median response time":
        labels_count = getLabelsCount(current_runId)
        height = str(int(int(int(labels_count)+2) * 35.2))
    url = ""
    if baseline_runId == None:
        url=grafana_server + "/render/d-solo/"+dash_id+\
        "?orgId=" + grafana_orgId + "&from="+tmp_start+"&to="+tmp_end+ \
        "&var-aggregation=60&var-sampleType=transaction&var-runId="+current_runId+ \
        "&var-testName="+testName+"&panelId="+panelId+"&width="+width+"&height="+height
    else:
        url=grafana_server + "/render/d-solo/"+dash_id+ \
        "?orgId=" + grafana_orgId + "&from=now-12M&to=now&var-aggregation=60&var-sampleType=transaction&var-current_runId="+\
        current_runId+"&var-baseline_runId="+baseline_runId+"&var-testName="+\
        testName+"&panelId="+panelId+"&width="+width+"&height="+height 
    try:    
        response = requests.get(url=url, headers=headers_grafana)
    except Exception as er:
        logging.warning('ERROR: downloading image from Grafana failed')
        logging.warning(er)
    if response.status_code == 200:
            image = base64.b64encode(response.content)
            putImageToAzure(metric, image, filename+".png", metrics_source, jmeter_images, hardware_images) 
    else:
        logging.info('ERROR: downloading image from Grafana failed, metric: ' + metric)
    
def getAllScreenshots(current_runId_start_tmp, current_runId_end_tmp, baseline_runId_start_tmp, baseline_runId_end_tmp, current_runId, baseline_runId, test_profile, jmeter_images, hardware_images):
    try:
        screenshots = open('./config/screenshots.json')
        screenshots = json.load(screenshots)
    except Exception as er:
        logging.warning('ERROR: failed to open screenshots.json file')
        logging.warning(er) 

    metrics_source = "JMeter metrics, current test"
    for metric in screenshots[metrics_source]:
        downloadScreenshot(metric, 
                           screenshots[metrics_source][metric]["dash_id"], 
                           str(current_runId_start_tmp), 
                           str(current_runId_end_tmp), 
                           current_runId, 
                           test_profile, 
                           screenshots[metrics_source][metric]["id"], 
                           current_runId + "_" + screenshots[metrics_source][metric]["filename"],
                           screenshots[metrics_source][metric]["width"], 
                           screenshots[metrics_source][metric]["height"],
                           metrics_source,
                           jmeter_images, 
                           hardware_images)
    
    logging.info("INFO: JMeter metrics for the "+current_runId+" test: done")
    
    metrics_source = "JMeter metrics, comparison"
    for metric in screenshots[metrics_source]:
        downloadScreenshot(metric, 
                           screenshots[metrics_source][metric]["dash_id"], 
                           str(current_runId_start_tmp), 
                           str(current_runId_end_tmp), 
                           current_runId, 
                           test_profile, 
                           screenshots[metrics_source][metric]["id"], 
                           current_runId + "_" + screenshots[metrics_source][metric]["filename"], 
                           screenshots[metrics_source][metric]["width"], 
                           screenshots[metrics_source][metric]["height"],
                           metrics_source,
                           jmeter_images, 
                           hardware_images, 
                           baseline_runId)
        
    logging.info("INFO: JMeter comparison metrics for the "+current_runId+" test: done")
    
    metrics_source = "Hardware metrics"
    if test_profile in screenshots[metrics_source]:
        for metric in screenshots[metrics_source][test_profile]:
            downloadScreenshot(metric, 
                            screenshots[metrics_source][test_profile][metric]["dash_id"], 
                            str(current_runId_start_tmp), 
                            str(current_runId_end_tmp), 
                            current_runId, 
                            test_profile, 
                            screenshots[metrics_source][test_profile][metric]["id"], 
                            current_runId + "_" + screenshots[metrics_source][test_profile][metric]["filename"], 
                            screenshots[metrics_source][test_profile][metric]["width"], 
                            screenshots[metrics_source][test_profile][metric]["height"],
                            metrics_source, 
                            jmeter_images, 
                            hardware_images)
        
        logging.info("INFO: Hardware metrics for the "+current_runId+" test: done")

    return jmeter_images, hardware_images
    

def createOrUpdatePage(path, page_content):
    content = { "content": page_content }
    wiki_api_url = azure_wiki_organization_url + "/"+azure_wiki_project+"/_apis/wiki/wikis/"+azure_wiki_identifier+"/pages?path="+path+"&api-version=6.0"
    try:
        response = requests.put(
            url=wiki_api_url, headers=headers_page,json=content)
    except Exception as er:
        logging.warning('ERROR: failed to upload the page to wiki')
        logging.warning(er)
    if "specified in the add operation already exists in the wiki" in str(response.content):
        try:
            response_get_page = requests.get(
                url=wiki_api_url, headers=headers_page)
        except Exception as er:
            logging.warning('ERROR: getting ETag failed')
            logging.warning(er)       
        headers_page["If-Match"]=str(response_get_page.headers["ETag"])
        try:
            response = requests.put(
            url=wiki_api_url, headers=headers_page,json=content)
        except Exception as er:
            logging.warning('ERROR: failed to update the page in wiki')
            logging.warning(er)
            
def getGrafanaLink(grafana_server, grafana_dashboard, grafana_orgId, start_tmp, end_tmp, runId, testName):
    url = grafana_server + grafana_dashboard + '?orgId=' + grafana_orgId + '&from='+str(start_tmp)+'&to='+str(end_tmp)+'&var-aggregation=60&var-sampleType=transaction&var-runId='+str(runId)+'&var-testName='+str(testName)
    return url      

        
def generateReport(current_runId, testName, baseline_runId = None):
    defineConfigVariables()
    if baseline_runId == None:
        baseline_runId = getBaselineRunId(testName) 
    current_runId_start_tmp = getTestStartTime(current_runId)
    current_runId_end_tmp = getTestEndTime(current_runId)
    baseline_runId_start_tmp = getTestStartTime(baseline_runId)
    baseline_runId_end_tmp = getTestEndTime(baseline_runId)
    current_test_grafana_link = getGrafanaLink(grafana_server, grafana_dashboard, grafana_orgId, current_runId_start_tmp, current_runId_end_tmp, current_runId, testName)
    baseline_test_grafana_link = getGrafanaLink(grafana_server, grafana_dashboard, grafana_orgId, baseline_runId_start_tmp, baseline_runId_end_tmp, baseline_runId, testName)
    current_runId_max_threads = getMaxThreads(current_runId)
    baseline_runId_max_threads = getMaxThreads(baseline_runId)
    jmeter_images, hardware_images = getAllScreenshots(current_runId_start_tmp, current_runId_end_tmp, baseline_runId_start_tmp, baseline_runId_end_tmp, current_runId, baseline_runId, testName, {}, {})
    azure_wiki_page_name = str(current_runId_max_threads) + " users | Azure candidate | " + str(datetime.utcfromtimestamp(current_runId_start_tmp/1000).strftime("%d-%m-%Y %I:%M %p"))
    
    #pmi
    azure_wiki_path_final = azure_wiki_path + "/" + testName + "/" + azure_wiki_page_name
    #getAzureAppInsightsLogs(current_runId_start_tmp, current_runId_end_tmp, current_runId)
    body = '''
##Status: `To fill in manually`

[[_TOC_]]

# Summary
 - To fill in manually

# Test settings
|vUsers| Ramp-up period | Duration | Start time | End time | Comments | Grafana dashboard |
|--|--|--|--|--|--|--|--|
|'''+str(current_runId_max_threads)+''' |600 sec|'''+str(int((current_runId_end_tmp/1000)-(current_runId_start_tmp/1000)))+''' sec |''' +str(datetime.utcfromtimestamp(current_runId_start_tmp/1000).strftime("%d-%m-%Y %I:%M %p"))+'''|'''+str(datetime.utcfromtimestamp(current_runId_end_tmp/1000).strftime("%d-%m-%Y %I:%M %p"))+'''| Current test | [Grafana link]('''+current_test_grafana_link+''') |
|'''+str(baseline_runId_max_threads)+''' |600 sec|'''+str(int((baseline_runId_end_tmp/1000)-(baseline_runId_start_tmp/1000)))+''' sec |''' +str(datetime.utcfromtimestamp(baseline_runId_start_tmp/1000).strftime("%d-%m-%Y %I:%M %p"))+'''|'''+str(datetime.utcfromtimestamp(baseline_runId_end_tmp/1000).strftime("%d-%m-%Y %I:%M %p"))+'''| Baseline test | [Grafana link]('''+baseline_test_grafana_link+''') |

# JMeter metrics
---
'''
    for image in jmeter_images:
        body = body + '''\n'''
        body = body + '''## ''' + str(image)
        body = body + '''\n'''
        body = body + '''![image.png](/.attachments/''' + str(jmeter_images[image]) + ''')'''
        body = body + '''\n'''
        body = body + '''\n'''
    
    body = body + '''# Hardware metrics
---
'''
    for image in hardware_images:
        body = body + '''\n'''
        body = body + '''## ''' + str(image)
        body = body + '''\n'''
        body = body + '''![image.png](/.attachments/''' + str(hardware_images[image]) + ''')'''
        body = body + '''\n'''
        body = body + '''\n'''
        
    createOrUpdatePage(azure_wiki_path_final, body)
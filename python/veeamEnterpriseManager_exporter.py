import time
import requests
from requests.sessions import Session
import base64
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
from urllib3.exceptions import InsecureRequestWarning
import os

#CONFIGURATION SECTION

veeamUsername = os.getenv('username')  #Your username, if using domain based account, please add it like user@domain.com (if you use domain\account it is not going to work!)
veeamPassword = os.getenv('password')
veeamRestServer = os.getenv('server-ip')
veeamRestPort = os.getenv('port')


#OPERATION
veeamJobSessions="100"
veeambase= (veeamUsername + ":" +veeamPassword)
veeamurl= "https://" + veeamRestServer + ":" + veeamRestPort +  '/api/sessionMngr/?v=latest'
authEncodedBytes= base64.b64encode(veeambase.encode("utf-8"))
veeamAuth=str(authEncodedBytes,"utf-8")

headers = {
    'Authorization': f"Basic {veeamAuth}",
    'Content-Length': '0',
    'Accept': 'application/json',
}

params = (
    ('v', 'latest'),
)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
response = requests.post (veeamurl , headers=headers, params=params, verify=False)


responseDict=response.json()
veeamSessionId= responseDict.get('SessionId')
sessionEncodedBytes= base64.b64encode(veeamSessionId.encode("utf-8"))
veeamXRestSvcSessionId=str(sessionEncodedBytes,"utf-8")
print(veeamXRestSvcSessionId)

###Overview Metrics
veeamEMUrl = "https://" + veeamRestServer + ":" + veeamRestPort + '/api/reports/summary/overview'

##Jobs Statistics
veeamJobUrl = "https://" + veeamRestServer + ":" + veeamRestPort + '/api/reports/summary/job_statistics'

#overview of virtual machines
#veeamVMUrl = "https://" + veeamRestServer + ":" + veeamRestPort + '/api/reports/summary/vms_overview'
#cookies = {
#    'X-RestSvcSessionId': veeamXRestSvcSessionId,
#}

#headers = {
#    'Accept': 'application/json',
#    'X-RestSvcSessionId': veeamXRestSvcSessionId,
#    'Content-Length': '0',
#}
#response = requests.get(veeamVMUrl, headers=headers, cookies=cookies, verify=False)
#vmOverviewResponse=response.json()



###Overview Metrics
def getMetrics():
        global veeamBackupServers
        global veeamRunningJobs
        global veeamScheduledJobs
        global veeamSuccessfulVmLastestStates
        global veeamWarningVmLatestStates
        global veeamFailedVmLastestStates

        cookies = {
            'X-RestSvcSessionId': veeamXRestSvcSessionId,
        }
        
        headers = {
            'Accept': 'application/json',
            'X-RestSvcSessionId': veeamXRestSvcSessionId,
            'Content-Length': '0',
        }
        response = requests.get(veeamEMUrl, headers=headers, cookies=cookies, verify=False)
        overviewResponse=response.json()
        veeamBackupServers=overviewResponse.get('BackupServers')
        veeamRunningJobs=overviewResponse.get('RunningJobs')
        veeamScheduledJobs=overviewResponse.get('ScheduledJobs')
        veeamSuccessfulVmLastestStates=overviewResponse.get('SuccessfulVmLastestStates')
        veeamWarningVmLatestStates=overviewResponse.get('WarningVmLastestStates')
        veeamFailedVmLastestStates=overviewResponse.get('FailedVmLastestStates')


#get job metrics 
def getJobMetrics():
        global veeamFailedJobRuns
        cookies = {
            'X-RestSvcSessionId': veeamXRestSvcSessionId,
        }
        
        headers = {
            'Accept': 'application/json',
            'X-RestSvcSessionId': veeamXRestSvcSessionId,
            'Content-Length': '0',
        }
        response = requests.get(veeamJobUrl, headers=headers, cookies=cookies, verify=False)
        jobsStaticResponse=response.json()
        veeamFailedJobRuns=jobsStaticResponse.get('FailedJobRuns')

# EXPOSE METRICS
class prometheusCollector(object):
    def __init__(self):
        pass
    def collect(self):
        getMetrics()
        getJobMetrics()
        backupservers = GaugeMetricFamily("veeamBackupServers", 'Help text', labels=['instance'])
        backupservers.add_metric(["VeeamEnterpriseManager"], veeamBackupServers)
        yield backupservers
        ScheduledJobs = GaugeMetricFamily("veeamScheduledJobs", 'Help text', labels=['instance'])
        ScheduledJobs.add_metric(["VeeamEnterpriseManager"], veeamScheduledJobs)
        yield ScheduledJobs
        RunningJobs = GaugeMetricFamily("veeamRunningJobs", 'Help text', labels=['instance'])
        RunningJobs.add_metric(["VeeamEnterpriseManager"], veeamRunningJobs)
        yield RunningJobs
        SuccessfulVmLastestStates = GaugeMetricFamily("veeamSuccessfulVmLastestStates", 'Help text', labels=['instance'])
        SuccessfulVmLastestStates.add_metric(["VeeamEnterpriseManager"], veeamSuccessfulVmLastestStates)
        yield SuccessfulVmLastestStates
        WarningVmLastestStates = GaugeMetricFamily("WarningVmLastestStates", 'Help text', labels=['instance'])
        WarningVmLastestStates.add_metric(["VeeamEnterpriseManager"], veeamWarningVmLatestStates)
        yield WarningVmLastestStates
        FailedVmLastestStates = GaugeMetricFamily("FailedVmLastestStates", 'Help text', labels=['instance'])
        FailedVmLastestStates.add_metric(["VeeamEnterpriseManager"], veeamFailedVmLastestStates)
        yield FailedVmLastestStates
        Veeam_FailedJobRuns = GaugeMetricFamily("Veeam_FailedJobRuns", 'Help text', labels=['instance'])
        Veeam_FailedJobRuns.add_metric(["VeeamEnterpriseManager"], veeamFailedJobRuns)
        yield Veeam_FailedJobRuns

#HTTP SERVER

if __name__ == '__main__':
    start_http_server(8000)

    REGISTRY.register(prometheusCollector())
    while True:
        getMetrics()
        getJobMetrics()
        time.sleep(180)
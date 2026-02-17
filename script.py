from urllib import request
import json
from prometheus_client import start_http_server, Counter, Gauge
from time import sleep
import logging
import os 

_BASE = "http://{0}/rest/v1/"

# Downstream
UNCORRECTABLE_ERR_COUNT = Gauge('docsis_ds_err_uncorrected_count', 'Downstream Uncorrected Error Rate', ['channel', 'channelType', 'lockStatus'])
CORRECTABLE_ERR_COUNT = Gauge('docsis_ds_err_corrected_count', 'Downstream Corrected Error Rate', ['channel', 'channelType', 'lockStatus'])

# Upstream
UPSTREAM_INFO_FREQ = Gauge('docsis_us_info_freq', 'DOCSIS Upstream Info', ['channel', 'lockStatus', 'symbolRate', 'modulation', 't1Timeout', 't2Timeout', 't3Timeout', 't4Timeout', 'channelType'])
UPSTREAM_INFO_POWER = Gauge('docsis_us_info_power', 'DOCSIS Upstream Info', ['channel', 'lockStatus', 'symbolRate', 'modulation', 't1Timeout', 't2Timeout', 't3Timeout', 't4Timeout', 'channelType'])

# Service Flow info
SERVICE_FLOW_INFO_RATE_MAX = Gauge('docsis_service_flow_traffic_rate_max', 'DOCSIS Service Info - Max Traffic Rate', ['serviceFlowId', 'direction', 'scheduleType'])
SERVICE_FLOW_INFO_BURST_MAX = Gauge('docsis_service_flow_traffic_burst', 'DOCSIS Service Flow - Max Burst Rate',     ['serviceFlowId', 'direction', 'scheduleType'])
SERVICE_FLOW_INFO_BURST_MIN = Gauge('docsis_service_flow_traffic_rate_min', 'DOCSIS Service Flow - Max Burst Rate',  ['serviceFlowId', 'direction', 'scheduleType'])

# Gateway Info
GATEWAY_INFO = Gauge('docsis_gateway_info', 'DOCSIS Gateway Info',  ['mode', 'macAddress', 'globalAddress', 'linkAddress', 'defaultGateway'])

# Gateway Info
REST_SERVER_ERR = Counter('docsis_http_server_err', 'REST Server',  ['statuscode'])

log_format = "%(asctime)s - %(levelname)s - [%(pathname)s] - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt='%Y-%m-%dT%H:%M:%S%z' 
)
logger = logging.getLogger(__name__)

class Metrics:
    def __init__(self, gw_url: str="http://192.168.0.1/rest/v1/"):
        self._url = gw_url
        self.handle = request

    def fetch_docsis_ds(self):
        stats = self._fetch_url(f"{self._url}cablemodem/downstream")
        if not stats:
            return 
        for ds_stat in stats.get("downstream", dict()).get("channels", []):
            UNCORRECTABLE_ERR_COUNT.labels(channel=ds_stat['channelId'], channelType=ds_stat['channelType'], lockStatus=ds_stat['lockStatus']).set(ds_stat['uncorrectedErrors'])
            CORRECTABLE_ERR_COUNT.labels(channel=ds_stat['channelId'], channelType=ds_stat['channelType'], lockStatus=ds_stat['lockStatus']).set(ds_stat['correctedErrors'])

    def fetch_docsis_us(self):
        stats = self._fetch_url(f"{self._url}cablemodem/upstream")
        if not stats:
            return 
        for us_stat in stats.get("upstream", dict()).get("channels", []):
            UPSTREAM_INFO_FREQ.labels(
                channel=us_stat['channelId'], lockStatus=us_stat['lockStatus'], 
                symbolRate=us_stat['symbolRate'],modulation=us_stat['modulation'],
                t1Timeout=us_stat['t1Timeout'],t2Timeout=us_stat['t2Timeout'],
                t3Timeout=us_stat['t3Timeout'],t4Timeout=us_stat['t4Timeout'],
                channelType=us_stat['channelType'],
            ).set(us_stat['frequency'])
            UPSTREAM_INFO_POWER.labels(
                channel=us_stat['channelId'], lockStatus=us_stat['lockStatus'], 
                symbolRate=us_stat['symbolRate'],modulation=us_stat['modulation'],
                t1Timeout=us_stat['t1Timeout'],t2Timeout=us_stat['t2Timeout'],
                t3Timeout=us_stat['t3Timeout'],t4Timeout=us_stat['t4Timeout'],
                channelType=us_stat['channelType'],
            ).set(us_stat['power'])

    def fetch_docsis_service_flows(self):
        stats = self._fetch_url(f"{self._url}cablemodem/serviceflows")
        if not stats:
            return 
        for service_flow in stats.get("serviceFlows",[]):
            service_flow = service_flow['serviceFlow']
            SERVICE_FLOW_INFO_RATE_MAX.labels(
                serviceFlowId=service_flow['serviceFlowId'], direction=service_flow['direction'], 
                scheduleType=service_flow['scheduleType'],
            ).set(service_flow['maxTrafficRate'])
            SERVICE_FLOW_INFO_BURST_MAX.labels(
                serviceFlowId=service_flow['serviceFlowId'], direction=service_flow['direction'], 
                scheduleType=service_flow['scheduleType'],
            ).set(service_flow['maxTrafficBurst'])
            SERVICE_FLOW_INFO_BURST_MIN.labels(
                serviceFlowId=service_flow['serviceFlowId'], direction=service_flow['direction'], 
                scheduleType=service_flow['scheduleType'],
            ).set(service_flow['maxConcatenatedBurst'])

    def fetch_system_provisioning(self):
        stats = self._fetch_url(f"{self._url}system/gateway/provisioning")
        if not stats:
            return 
        stats = stats.get('provisioning', dict())
        GATEWAY_INFO.labels(
            mode=stats['mode'], macAddress=stats['macAddress'],
            globalAddress=stats['ipv6']['globalAddress'], linkAddress=stats['ipv6']['linkAddress'],
            defaultGateway=stats['ipv6']['defaultGateway'],
        ).set(1)

    def _inc_req(self, url):
        REST_SERVER_ERR.labels(statuscode=url.code).inc()

    def _fetch_url(self, url: str) -> dict:
        r = request.urlopen(url)
        self._inc_req(r)
        if r.code != 200:
            return dict()
        return json.loads(r.read().decode())

def main(gw_ip: str):
    m = Metrics(_BASE.format(gw_ip))
    while True:
        m.fetch_docsis_ds()
        m.fetch_docsis_us()
        m.fetch_docsis_service_flows()
        m.fetch_system_provisioning()
        sleep(30)

if __name__ == "__main__":
    gw = os.getenv("GATEWAY_IP", "192.168.0.1")
    bind_addr = os.getenv("LISTEN_IP", "0.0.0.0")
    listen_port = os.getenv("LISTEN_PORT", "8000")
    start_http_server(port=int(listen_port), addr=bind_addr)
    logging.info(f"bind: {bind_addr}, port: {listen_port}, gw: {gw}")
    main(gw)

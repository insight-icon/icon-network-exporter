import json

from requests.exceptions import RequestException
import requests
from prometheus_client import Counter
from icon_network_exporter import config


class iconRPCError( RuntimeError ):
    pass


class iconRPC:
    """
    Class interacts with an icon node via RPC and takes care of errors.
    """

    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self._next_id = 1
        self._counter_discovery_node = Counter('icon_counter_discovery_node','Total number of calls to edge')
        self._counter_discovery_node_error = Counter('icon_counter_discovery_node_error','Total number of call errors to edge')
        self._counter_rpc_node_reply_status = Counter('icon_counter_node_reply_status','Total number of OK reply',["node_ID","name","status"])


    def request_nothrow_discovery_node(self, request_data):
        self._next_id += 1
        self._counter_discovery_node.inc()
        try:
            result = requests.post(self.rpc_url, data=json.dumps(config.request_data))
        except RequestException:
            # TODO more fine-grained error handling
            self._counter_discovery_node_error.inc()
            return
        if result.status_code != 200:
            self._counter_discovery_node_error.inc()
            return
        result_json = result.json()
        if result_json.get( 'error' ):
            self._counter_discovery_node_error.inc()
            return
        return result_json

    def discovery_node_post_request(self, request_data, params=None):
        result = self.request_nothrow_discovery_node(request_data)
        if result is None:
            raise iconRPCError()
        return result

    def node_get_request(self,IP_port,name):
        node_IP=IP_port[:IP_port.rfind(":")]
        # print ("pass",node_IP)
        try:
            result = requests.get('http://'+node_IP+':9000/api/v1/status/peer', timeout=0.3)
            self._counter_rpc_node_reply_status.labels(node_IP,name[0],'ok').inc()
            # print(result)
        except RequestException:
            # TODO more fine-grained error handling
            # print("exeption", node_IP)
            self._counter_rpc_node_reply_status.labels(node_IP,name[0],'Error').inc()
            # self._counter_network_error.inc()
            return None

        if result.status_code != 200:
            # print("status error")
            self._counter_rpc_node_reply_status.labels(node_IP,name[0],'Error').inc()
            return None

        result_json = result.json()
        if result_json.get( 'error' ):
            # print("status error")
            self._counter_rpc_node_reply_status.labels(node_IP,name[0],'Error').inc()
            return None
        if result is None:
            raise iconRPCError()
            return None
        return result_json

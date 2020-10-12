from abc import abstractmethod
from datetime import datetime
import requests
import concurrent.futures
from icon_network_exporter._utils import PeriodicTask, check
from prometheus_client import Gauge
from icon_network_exporter import config


class ExporterPeriodicTask(PeriodicTask):
    """
    PeriodicTask.
    """

    def __init__(self, rpc, period_seconds):
        super(ExporterPeriodicTask, self).__init__(period_seconds)
        self._rpc = rpc

    #
    def _perform(self):
        self._perform_internal()
        # try:
        #     self._perform_internal()
        # except:
        #     pass

    #
    @abstractmethod
    def _perform_internal(self):
        raise NotImplementedError()


#
class PrepsUpdater(ExporterPeriodicTask):
    def __init__(self, rpc, request_data):
        super(PrepsUpdater, self).__init__(rpc, 3)
        self.request_data = request_data
        self._gauge_preps_discovery_blockHeight = Gauge('icon_preps_blockHeight', '------node block height',
                                                        ['p2pEndpoint', 'name', 'block_height'])
        self._gauge_preps_discovery_node_rank = Gauge('icon_preps_node_rank', '------rank of node',
                                                      ['p2pEndpoint', 'name'])
        # self._gauge_preps_discovery_node_count = Gauge('icon_preps_nodeCount', '------the Count of nodes in network')
        self._gauge_node_reference_blockHeight = Gauge('icon_node_reference__blockHeight',
                                                       '------reference block height',
                                                       ['block_height'])
        self._nodes_list = {}  # pairs of node ID and a list of block_height,epoch_height,total_tx,peer_count
        self._allpreps = None
        self._request_counter = 0

    def _perform_internal(self):
        print("------------")
        print("internal Performer")
        self._get_prep_list()

        self._nodeRank = 1

        # Parallelize requests

        for node in self._allpreps:
            IP_address = str(node["p2pEndpoint"])
            self._nodes_list.update({IP_address: [node["name"], self._nodeRank]})
            self._gauge_preps_discovery_blockHeight.labels(IP_address[:IP_address.rfind(":")], node["name"], 1).set(
                int(node["blockHeight"], 16))
            self._gauge_preps_discovery_node_rank.labels(IP_address[:IP_address.rfind(":")], node["name"]).set(
                self._nodeRank)
            self._nodeRank += 1
        # self._gauge_preps_discovery_node_count.set(self._nodeRank - 1)

        for IP, value in self._nodes_list.items():



            result = self._rpc.node_get_request(IP, value)

            if result != None:
                node_IP = IP[:IP.rfind(":")]
                self._gauge_node_reference_blockHeight.labels(node_IP, value[0], value[1]).set(result["block_height"])
            #     # self._gauge_node_reference_total_tx.labels(node_IP,self._nodes_list[node_IP]).set(result["total_tx"])


    def _get_prep_list(self):

        if not self._allpreps or self._request_counter % 60 == 0:
            self._allpreps = (self._rpc.discovery_node_post_request()["result"]["preps"])
            self._request_counter += 1

    def update_block_height(self):
        pass

    def load_url(url, timeout):
        return requests.get(url, timeout = timeout)

    def get_response_from_nodes(self):
        print()
        # with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        #
        #     future_to_url = {executor.submit(requests.get(url, self.), url, 10): url for url in get_urls()}
        #     for future in concurrent.futures.as_completed(future_to_url):
        #         url = future_to_url[future]
        #         try:
        #             data = future.result()
        #         except Exception as exc:
        #             resp_err = resp_err + 1
        #         else:
        #             resp_ok = resp_ok + 1
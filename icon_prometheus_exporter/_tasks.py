from abc import abstractmethod
from datetime import datetime

from icon_prometheus_exporter._utils import PeriodicTask, check
from prometheus_client import Gauge
from icon_prometheus_exporter import config


class ExporterPeriodicTask(PeriodicTask):
    """
    PeriodicTask.
    """

    def __init__(self, rpc, period_seconds):
        super(ExporterPeriodicTask, self).__init__(period_seconds)
        self._rpc = rpc
    #
    def _perform(self):
        try:
            self._perform_internal()
        except:
            pass
    #
    @abstractmethod
    def _perform_internal(self):
        raise NotImplementedError()
#
class prepsUpdater(ExporterPeriodicTask):
    def __init__(self, rpc, request_data):
        super(prepsUpdater, self).__init__(rpc, 3)
        self.request_data = request_data
        self._gauge_preps_discovery_blockHeight = Gauge('icon_preps_blockHeight', '------the hight of block chain',
                                              ['p2pEndpoint','name','rank'])
        self._gauge_preps_discovery_node_count = Gauge('icon_preps_nodeCount', '------the Count of nodes in network')
        self._gauge_node_reference_blockHeight = Gauge('icon_node_reference__blockHeight', '------the blockHeight data from icon nodes',
                                              ['nodeID','name','rank','time'])
        self._nodes_list = {} # pairs of node ID and a list of block_height,epoch_height,total_tx,peer_count
    def _perform_internal(self):
        print("------------")
        print( "internal Performer" )

        # scrap the all nodes informations from the discovery Node
        self._allpreps = (self._rpc.discovery_node_post_request(self.request_data)["result"]["preps"])
        # print (self._allpreps)
        self._nodeRank = 1
        for node in self._allpreps:
            # print (node)
            IP_address = str(node["p2pEndpoint"])
            # print (IP_address)
            # print()
            self._nodes_list.update({IP_address:[node["name"],self._nodeRank]})
            self._gauge_preps_discovery_blockHeight.labels(IP_address[:IP_address.rfind(":")],node["name"],self._nodeRank).set(
                int(node["blockHeight"], 16))
            self._nodeRank += 1
        self._gauge_preps_discovery_node_count.set(self._nodeRank-1)
        # print (self._nodes_list)


        c = 0
        for IP,value in self._nodes_list.items():
            # print(IP,value)
            # print()
            result = self._rpc.node_get_request(IP,value)
            # print ("dddd",result)
            if result != None:
                node_IP=IP[:IP.rfind(":")]
                # print (node_IP)
                self._gauge_node_reference_blockHeight.labels(node_IP,value[0],value[1],datetime.now()).set(result["block_height"])
            #     # self._gauge_node_reference_total_tx.labels(node_IP,self._nodes_list[node_IP]).set(result["total_tx"])
        # print(c)


    def update_Blockhight(self):
        pass

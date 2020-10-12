# Prometheus exporter for icon blockchain network
# Scrapes metrics from all the nodes in the network and exposes them
# to be scraped by prometheus

from prometheus_client import start_http_server
from prometheus_client import Gauge
import requests
from signal import signal, SIGINT, SIGTERM
import asyncio

from time import sleep, time

from icon_network_exporter2.config import Config
from icon_network_exporter2.exceptions import IconRPCError
from icon_network_exporter2.utils import get_prep_list_async


GET_PREPS_RPC = {
    "jsonrpc": "2.0",
    "id": 1234,
    "method": "icx_call",
    "params": {
        "to": "cx0000000000000000000000000000000000000000",
        "dataType": "call",
        "data": {
            "method": "getPReps",
            "params": {
                "startRanking": "0x1",
                "endRanking": "0x64"
            }
        }
    }
}


class Exporter:
    def __init__(self, config: Config = Config()):

        self.config = config
        self.exporter_port = config.exporter_port
        self.exporter_address = config.exporter_address
        self.discovery_node_rpc_url = config.discovery_node_rpc_url

        self.last_processed_block_num = None
        self.last_processed_block_hash = None

        self.gauge_prep_block_height = Gauge('icon_preps_blockHeight', '------node block height',
                                            ['name', 'address', 'block_height'])

        self.gauge_prep_node_rank = Gauge('icon_preps_node_rank', '------rank of node',
                                          ['name', 'address', 'rank'])

        self.gauge_node_reference_blockHeight = Gauge('icon_node_reference__blockHeight',
                                                      '------reference block height',
                                                      ['name', 'address', 'block_height'])

        self.gauge_highest_block = Gauge('icon_highest_block',
                                         'Number of the highest block in chain as seen by current node')

        self.prep_list: list = []
        self.prep_urls: list = []
        self.prep_list_request_counter: int = 0

    def serve_forever(self):
        start_http_server(6100, self.exporter_address)
        stop = [False]

        def set_stop(_number, _frame):
            stop[0] = True

        signal(SIGINT, set_stop)
        signal(SIGTERM, set_stop)

        while not stop[0]:
            next_iteration_time = time() + self.config.poll_interval
            try:
                self._run_updaters()
            except IconRPCError:
                pass

            delay = next_iteration_time - time()
            if delay > 0:
                sleep(delay)

    def _run_updaters(self):
        self.get_prep_list()
        self.get_reference()
        self.scrape_metrics()
        self.summarize_metrics()

    def get_prep_list(self):
        if not self.prep_list or self.prep_list_request_counter % self.config.refresh_prep_list_count == 0:
            self.prep_list = requests.post(self.config.discovery_node_rpc_url, json=GET_PREPS_RPC).json()["result"][
                "preps"]

            for i, v in enumerate(self.prep_list):
                self.prep_list[i]['apiEndpoint'] = ''.join(['http://', v['p2pEndpoint'].split(':')[0], ':9000/api/v1/status/peer'])
                self.gauge_prep_node_rank.labels(v['name'], v['address'], i)
            self.prep_list_request_counter += 1

    def get_reference(self):
        pass

    def scrape_metrics(self):
        resp = asyncio.run(get_prep_list_async(self.prep_list))
        for i in resp:
            if i:
                name = next(item for item in self.prep_list if item['apiEndpoint'] == i['apiEndpoint'])['name']
                self.gauge_prep_block_height.labels(name, i['apiEndpoint'], i['block_height'])

    def summarize_metrics(self):
        pass

def main():
    config = Config()
    e = Exporter(config)
    e.serve_forever()


if __name__ == '__main__':
    main()

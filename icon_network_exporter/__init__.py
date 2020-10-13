# Prometheus exporter for icon blockchain network
# Scrapes metrics from all the nodes in the network and exposes them
# to be scraped by prometheus

from prometheus_client import start_http_server
from prometheus_client import Gauge
import requests
from signal import signal, SIGINT, SIGTERM
import asyncio
# from types import long

from time import sleep, time

from icon_network_exporter.config import Config
from icon_network_exporter.exceptions import IconRPCError
from icon_network_exporter.utils import get_prep_list_async, get_highest_block

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

RPC_URL_MAP = {
    'mainnet': {
        'main_api_endpoint': 'https://ctz.solidwallet.io/api/v3',
        'reference_nodes': [],
    },
    'zicon': {
        'main_api_endpoint': 'https://zicon.net.solidwallet.io/api/v3',
        'reference_nodes': [],
    }
}


class Exporter:
    def __init__(self, config: Config):

        self.config = config
        self.exporter_port = config.exporter_port
        self.exporter_address = config.exporter_address

        if not self.config.main_api_endpoint:
            self.config.main_api_endpoint = RPC_URL_MAP[self.config.network_name]['main_api_endpoint']

        self.last_processed_block_num = None
        self.last_processed_block_hash = None

        self.gauge_prep_block_height = Gauge('icon_preps_block_height', '------node block height',
                                             ['name'])

        self.gauge_prep_node_rank = Gauge('icon_preps_node_rank', '------rank of node',
                                          ['name', 'address'])

        self.gauge_node_reference_blockHeight = Gauge('icon_node_reference__blockHeight',
                                                      '------reference block height',
                                                      ['name', 'address'])

        self.gauge_highest_block = Gauge('icon_highest_block',
                                         'Number of the highest block in chain as seen by current node')

        self.gauge_total_tx = Gauge('icon_total_tx',
                                    'Total number of transactions')


        self.prep_list: list = []
        self.prep_urls: list = []
        self.prep_list_request_counter: int = 0
        from typing import List
        self.resp: List[List] = [[]]

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
        self.scrape_metrics()
        self.get_reference()
        self.summarize_metrics()

    def get_prep_list(self):
        if not self.prep_list or self.prep_list_request_counter % self.config.refresh_prep_list_count == 0:
            self.prep_list = requests.post(self.config.main_api_endpoint, json=GET_PREPS_RPC).json()["result"][
                "preps"]

            for i, v in enumerate(self.prep_list):
                self.prep_list[i]['apiEndpoint'] = ''.join(
                    ['http://', v['p2pEndpoint'].split(':')[0], ':9000/api/v1/status/peer'])
                self.gauge_prep_node_rank.labels(v['name'], v['address']).set(i)
            self.prep_list_request_counter += 1

    def scrape_metrics(self):
        self.resp.insert(0, asyncio.run(get_prep_list_async(self.prep_list)))
        if len(self.resp) >= self.config.num_data_points_retentation:
            self.resp.pop()

        self.resp[0] = [i for i in self.resp[0] if i is not None]
        for i in self.resp[0]:
            if i:
                name = next(item for item in self.prep_list if item['apiEndpoint'] == i['apiEndpoint'])['name']
                self.gauge_prep_block_height.labels(name).set(i['block_height'])

    def get_reference(self):
        # Get reference
        highest_block, reference_node_api_endpoint = get_highest_block(self.prep_list, self.resp[0])
        self.gauge_highest_block.set(highest_block)

        # Get total TX
        self.gauge_total_tx.set(next(item for item in self.resp[0] if item['apiEndpoint'] == reference_node_api_endpoint)['total_tx'])



    def summarize_metrics(self):
        pass


def main():
    config = Config()
    print(config)
    e = Exporter(config)
    e.serve_forever()


if __name__ == '__main__':
    main()

# Prometheus exporter for icon blockchain network
# Scrapes metrics from all the nodes in the network and exposes them
# to be scraped by prometheus

from prometheus_client import start_http_server
from prometheus_client import Gauge
import requests
from signal import signal, SIGINT, SIGTERM
import asyncio
from typing import List

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

STATUS_MAP = {
    'BlockGenerate': 0,
    'Vote': 1,
    'Watch': 2,
    'SubscribeNetwork': 3,
    'BlockSync': 4,
    'EvaluateNetwork': 5,
    'InitComponents': 6,
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

        self.gauge_prep_block_height = Gauge('icon_prep_block_height',
                                             'Node block height',
                                             ['name'])
        self.gauge_prep_status = Gauge('icon_prep_status', 'Number to indicate node status - ie Vote=1, Watch=2',
                                       ['name'])

        self.gauge_prep_node_rank = Gauge('icon_prep_node_rank', 'Rank of the node', ['name', 'address'])

        self.gauge_prep_node_block_time = Gauge('icon_prep_block_time', 'Time in seconds per block for a node',
                                                ['name'])

        self.gauge_node_reference_block_height = Gauge('icon_prep_reference__block_height',
                                                       'Block height of reference node',
                                                       ['name'])

        self.gauge_node_reference_block_time = Gauge('icon_node_reference__block_time',
                                                     'Time in seconds per block',
                                                     ['name', 'address'])

        self.gauge_total_tx = Gauge('icon_total_tx',
                                    'Total number of transactions')

        self.gauge_total_active_main_preps = Gauge('icon_total_active_main_preps',
                                                   'Total number of transactions')

        self.gauge_total_inactive_validators = Gauge('icon_total_inactive_validators',
                                                     'Total number of inactive validators - (nodes off / in blocksync)')

        self.prep_list: list = []
        self.prep_urls: list = []
        self.prep_list_request_counter: int = 0
        self.resp: List[List] = []
        self.resp_non_null: List[List] = []
        print(f"Running on {self.config.network_name} network")

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
        print(f"Iteration #{self.prep_list_request_counter}")
        self.get_prep_list()
        self.scrape_metrics()
        # self.get_active_preps()
        self.get_reference()
        self.summarize_metrics()

    def get_prep_list(self):
        if self.prep_list_request_counter % self.config.refresh_prep_list_count == 0:
            self.prep_list = requests.post(self.config.main_api_endpoint, json=GET_PREPS_RPC).json()["result"][
                "preps"]

            for i, v in enumerate(self.prep_list):
                self.prep_list[i]['apiEndpoint'] = ''.join(
                    ['http://', v['p2pEndpoint'].split(':')[0], ':9000/api/v1/status/peer'])
                self.gauge_prep_node_rank.labels(v['name'], v['address']).set(i)
        self.prep_list_request_counter += 1

    def scrape_metrics(self):
        self.resp.insert(0, asyncio.run(get_prep_list_async(self.prep_list)))
        self.resp_non_null.insert(0, [i for i in self.resp[0] if i is not None])
        if len(self.resp) > self.config.num_data_points_retentation:
            self.resp.pop()
            self.resp_non_null.pop()

        for i in self.resp_non_null[0]:
            if i:
                name = next(item for item in self.prep_list if item['apiEndpoint'] == i['apiEndpoint'])['name']
                self.gauge_prep_block_height.labels(name).set(i['block_height'])
                self.gauge_prep_status.labels(name).set(STATUS_MAP[i['state']])




    def get_reference(self):
        # Get reference
        highest_block, self.reference_node_api_endpoint = get_highest_block(self.prep_list, self.resp_non_null[0])
        reference_node_name = next(item for item in self.resp_non_null[0] if item['apiEndpoint'] == self.reference_node_api_endpoint)[
            'apiEndpoint']
        self.gauge_node_reference_block_height.labels(reference_node_name).set(highest_block)

        # Get total TX
        self.gauge_total_tx.set(
            next(item for item in self.resp_non_null[0] if item['apiEndpoint'] == self.reference_node_api_endpoint)[
                'total_tx'])

    def summarize_metrics(self):
        if len(self.resp_non_null) == self.config.num_data_points_retentation:
            # Instance summary
            for i, v in enumerate(self.resp_non_null[0]):
                # We're going to take the current block and subtract the block height
                # from the same address from a previous sample. That sample might not exist
                # so need to check first.
                current_block = self.resp_non_null[0][i]['block_height']

                previous_block = None
                for j in self.resp_non_null[self.config.num_data_points_retentation - 1]:
                    if j['apiEndpoint'] == self.resp_non_null[0][i]['apiEndpoint']:
                        previous_block = j['block_height']
                if previous_block:
                    num_blocks = current_block - previous_block
                    if num_blocks > 0:
                        block_time = (self.config.poll_interval * self.config.num_data_points_retentation) / num_blocks

                        prep_data = next(item for item in self.prep_list if
                                         item['apiEndpoint'] == self.resp_non_null[0][i]['apiEndpoint'])

                        self.gauge_prep_node_block_time.labels(prep_data['name']).set(block_time)
                        if self.resp_non_null[0][i]['apiEndpoint'] == self.reference_node_api_endpoint:
                            self.gauge_node_reference_block_time.labels(prep_data['name'], prep_data['address']).set(
                                block_time)


def main():
    config = Config()
    print(config)
    e = Exporter(config)
    e.serve_forever()


if __name__ == '__main__':
    main()

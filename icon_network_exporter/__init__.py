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
from icon_network_exporter.utils import get_prep_list_async, get_highest_block, get_rpc_attributes
from icon_network_exporter.rpc import get_preps_rpc, get_iiss_info

STATE_MAP = {
    'BlockGenerate': 0,
    'Vote': 1,
    'Watch': 2,
    'SubscribeNetwork': 3,
    'BlockSync': 4,
    'LeaderComplain': 5,
    'EvaluateNetwork': 6,
    'InitComponents': 7,
}


class Exporter:
    def __init__(self, config: Config):

        self.config = config

        self.last_processed_block_num = None
        self.last_processed_block_hash = None

        self.gauge_prep_node_block_height = Gauge('icon_prep_node_block_height',
                                                  'Node block height',
                                                  ['name', 'network_name'])
        self.gauge_prep_node_state = Gauge('icon_prep_node_state', 'Number to indicate node state - ie Vote=1, Watch=2',
                                           ['name', 'network_name'])

        self.gauge_prep_node_rank = Gauge('icon_prep_node_rank', 'Rank of the node', ['name', 'network_name'])

        self.gauge_prep_node_block_time = Gauge('icon_prep_node_block_time', 'Time in seconds per block for a node',
                                                ['name', 'network_name'])

        self.gauge_prep_node_latency = Gauge('icon_prep_node_latency', 'Time in seconds per for get request to node',
                                             ['name', 'network_name'])

        self.gauge_prep_reference_block_height = Gauge('icon_prep_reference_block_height',
                                                       'Block height of reference node', ['network_name'])

        self.gauge_prep_reference_block_time = Gauge('icon_prep_reference_block_time',
                                                     'Time in seconds per block', ['network_name'])

        self.gauge_total_tx = Gauge('icon_total_tx',
                                    'Total number of transactions', ['network_name'])

        self.gauge_blocks_left_in_term = Gauge('icon_blocks_left_in_term',
                                               'Number of blocks left in term', ['network_name'])

        self.gauge_total_active_main_preps = Gauge('icon_total_active_main_preps',
                                                   'Total number of active nodes above rank 22', ['network_name'])

        self.gauge_total_active_sub_preps = Gauge('icon_total_active_sub_preps',
                                                  'Total number of active validators - (Watch / Vote / BlockGenerate)',
                                                  ['network_name'])

        self.gauge_total_inactive_sub_preps = Gauge('icon_total_inactive_sub_preps',
                                                    'Total number of inactive validators - (nodes off / in blocksync)',
                                                    ['network_name'])

        self.prep_list: list = []
        self.prep_urls: list = []
        self.prep_list_request_counter: int = 0
        self.resp: List[List] = []
        self.resp_non_null: List[List] = []
        self.reference_list: List[List] = []
        print(f"Running on {self.config.network_name.value} network")

    def serve_forever(self):
        start_http_server(self.config.exporter_port, self.config.exporter_address)
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
        self.get_active_preps()
        self.get_reference()
        self.summarize_metrics()

    def get_prep_list(self):
        if self.prep_list_request_counter % self.config.refresh_prep_list_count == 0:
            self.prep_list = requests.post(self.config.main_api_endpoint,
                                           json=get_preps_rpc(self.config.end_ranking)).json()["result"]["preps"]
            for i, v in enumerate(self.prep_list):
                self.prep_list[i]['apiEndpoint'] = ''.join(
                    ['http://', v['p2pEndpoint'].split(':')[0], ':9000/api/v1/status/peer'])
                self.gauge_prep_node_rank.labels(v['name'], self.config.network_name.value).set(i)
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
                self.gauge_prep_node_block_height.labels(name, self.config.network_name.value).set(i['block_height'])
                self.gauge_prep_node_latency.labels(name, self.config.network_name.value).set(i['latency'])
                self.gauge_prep_node_state.labels(name, self.config.network_name.value).set(STATE_MAP[i['state']])

    def get_active_preps(self):
        active_main_preps = 0
        active_sub_preps = 0
        for prep in range(0, int(self.config.end_ranking, 16) - 1):
            state = None
            for i, v in enumerate(self.resp_non_null[0]):
                if self.prep_list[prep]['apiEndpoint'] == self.resp_non_null[0][i]['apiEndpoint']:
                    state = self.resp_non_null[0][i]['state']
                    break
            # resp_lookup = next(item for item in self.resp_non_null[0] if item['apiEndpoint'] == self.prep_list[i]['apiEndpoint'])
            # state = resp_lookup['state'] if 'state' in resp_lookup else None
            if state:
                if STATE_MAP[state] < 2 and prep < 22:
                    active_main_preps += 1
                if STATE_MAP[state] < 3 and prep >= 22:
                    active_sub_preps += 1

        self.gauge_total_active_main_preps.labels(self.config.network_name.value).set(active_main_preps)
        self.gauge_total_active_sub_preps.labels(self.config.network_name.value).set(active_sub_preps)
        self.gauge_total_inactive_sub_preps.labels(self.config.network_name.value).set(78 - active_sub_preps)

    def get_reference(self):
        # Get reference
        highest_block, self.reference_node_api_endpoint = get_highest_block(self.prep_list, self.resp_non_null[0])
        # reference_node_name = next(item for item in self.resp_non_null[0] if item['apiEndpoint'] == self.reference_node_api_endpoint)[
        #     'apiEndpoint']
        self.gauge_prep_reference_block_height.labels(self.config.network_name.value).set(highest_block)

        # self.reference_list.insert(0, get_rpc_attributes())
        # if len(self.reference_list) > self.config.num_data_points_retentation:
        #     self.reference_list.pop()

        total_tx = \
        next(item for item in self.resp_non_null[0] if item['apiEndpoint'] == self.reference_node_api_endpoint)[
            'total_tx']
        # Get total TX
        self.gauge_total_tx.labels(self.config.network_name.value).set(total_tx)

        term_change_block = requests.post(self.config.main_api_endpoint,
                                          json=get_iiss_info()).json()['result']['nextCalculation']

        self.gauge_blocks_left_in_term.labels(self.config.network_name.value).set(int(term_change_block, 16) - highest_block)

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
                        # Adding half a block to account for mid block sample
                        block_time = (self.config.poll_interval * self.config.num_data_points_retentation) / (
                            num_blocks)

                        prep_data = next(item for item in self.prep_list if
                                         item['apiEndpoint'] == self.resp_non_null[0][i]['apiEndpoint'])

                        self.gauge_prep_node_block_time.labels(prep_data['name'], self.config.network_name.value).set(
                            block_time)
                        if self.resp_non_null[0][i]['apiEndpoint'] == self.reference_node_api_endpoint:
                            # prep_data['name'], prep_data['address']
                            self.gauge_prep_reference_block_time.labels(self.config.network_name.value).set(block_time)


def main():
    config = Config()
    print(config)
    e = Exporter(config)
    e.serve_forever()


if __name__ == '__main__':
    main()

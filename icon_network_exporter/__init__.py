# Prometheus exporter for icon relay chain node

# TODO WebSocket subscriptions

import sys
import os

sys.path.append("..")
import argparse

from icon_network_exporter import _tasks
from icon_network_exporter._tasks import PrepsUpdater
from prometheus_client import start_http_server
from icon_network_exporter import config
# from icon_network_exporter.config import Config
from prometheus_client import Gauge

if __name__ == '__main__':
    # have to make sure we'll be able to find submodules
    sys.path.append(os.path.realpath(os.path.dirname(os.path.dirname(__file__))))

from icon_network_exporter._utils import check
from icon_network_exporter._rpc import iconRPC, iconRPCError
from icon_network_exporter.config import Config

class Exporter:
    POLL_INTERVAL = 0.5

    # def __init__(self, exporter_port='6100', exporter_address='', rpc_url=config.discovery_node_rpc_url):
    def __init__(self, config: Config = Config()):
        self.config = config
        self.exporter_port = config.exporter_port
        self.exporter_address = config.exporter_address
        # self.rpc = iconRPC(config)

        self._last_processed_block_num = None
        self._last_processed_block_hash = None

        self._gauge_highest_block = Gauge('polkadot_highest_block',
                                          'Number of the highest block in chain as seen by current node')

        # self.request_data = request_data
        self._info_updaters = [PrepsUpdater(self._rpc, self.request_data)]

    def serve_forever(self):
        start_http_server(6100, self.exporter_address)
        while True:
            try:
                self._run_updaters()
            except iconRPCError:
                pass

    def _run_updaters(self):
        
        for updater in self._info_updaters:
            updater.run()

# def parse_args(args):
#     ap = argparse.ArgumentParser(description='Prometheus python exporter for icon node')
#     ap.add_argument("--exporter_port", type=int, default=6100, help='expose metrics on this port')
#     ap.add_argument("--exporter_address", type=str, default='127.0.0.1', help='expose metrics on this address')
#     ap.add_argument("--rpc_url", type=str, default=config.discovery_node_rpc_url, help='discovery node rpc url')
#     return ap.parse_args(args)


def main():
    # args = parse_args(sys.argv[1:])
    # Exporter(args.exporter_port, args.exporter_address if args.exporter_address else '', args.rpc_url).serve_forever()
    config = Config()
    Exporter(config)


if __name__ == '__main__':
    main()

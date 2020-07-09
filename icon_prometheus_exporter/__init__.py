# Prometheus exporter for icon relay chain node

# TODO WebSocket subscriptions

import sys
import os
sys.path.append("..")
import argparse



from icon_prometheus_exporter import _tasks
from icon_prometheus_exporter._tasks import prepsUpdater
from prometheus_client import start_http_server
from icon_prometheus_exporter import config
if __name__ == '__main__':
    # have to make sure we'll be able to find submodules
    sys.path.append( os.path.realpath( os.path.dirname( os.path.dirname( __file__ ) ) ) )

from icon_prometheus_exporter._utils import check
from icon_prometheus_exporter._rpc import iconRPC, iconRPCError


class Exporter:
    POLL_INTERVAL = 0.5

    def __init__(self, exporter_port, exporter_address='', rpc_url='', request_data=''):
        self.exporter_port = exporter_port
        self.exporter_address = exporter_address
        self._rpc = iconRPC(rpc_url)
        self.request_data = request_data
        self._info_updaters = [prepsUpdater( self._rpc, self.request_data )]

    def serve_forever(self):
        start_http_server(6100)
        stop = [False]
        while not stop[0]:
            try:
                self._step()
            except iconRPCError:
                pass
            except iconRPCError:
                pass

    def _step(self):
        self._run_updaters()
#
    def _run_updaters(self):
        for updater in self._info_updaters:
            updater.run()


def main():
    ap = argparse.ArgumentParser( description='Prometheus python exporter for icon node' )
    ap.add_argument( "--exporter_port", type=int, default=6100, help='expose metrics on this port' )
    ap.add_argument( "--exporter_address", type=str, help='expose metrics on this address' )
    ap.add_argument( "--rpc_url", type=str, default=config.discovery_node_rpc_url, help='discovery node rpc url' )
    args = ap.parse_args()
    print(args)
    Exporter(args.exporter_port, args.exporter_address if args.exporter_address else '', args.rpc_url, config.request_data).serve_forever()


if __name__ == '__main__':
    main()

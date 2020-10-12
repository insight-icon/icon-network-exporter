from enum import Enum
from typing import Any
from pydantic import BaseSettings


discovery_node_rpc_url = 'https://ctz.solidwallet.io/api/v3'

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

DISCOVERY_NODE_RPC_URL_MAP = {
    'mainnet': 'https://ctz.solidwallet.io/api/v3',
    'zicon': 'https://zicon.ctz.solidwallet.io/api/v3',
}


class NetworksEnum(str, Enum):
    mainnet = 'mainnet'
    zicon = 'zicon'


class Config(BaseSettings):

    network_name: NetworksEnum = NetworksEnum.mainnet
    exporter_port: int = 6100
    exporter_address: str = ''
    get_preps_rpc: dict = GET_PREPS_RPC


    discovery_node_rpc_url: str = DISCOVERY_NODE_RPC_URL_MAP[network_name]

    parallelism: int = 1

    def __init__(self, **values: Any):
        super().__init__(**values)
        # if
        #

if __name__ == '__main__':
    c = Config()
    print(c.network_name)


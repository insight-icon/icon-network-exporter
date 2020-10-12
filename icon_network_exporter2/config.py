from enum import Enum
from typing import Any
from pydantic import BaseSettings

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

    discovery_node_rpc_url: str = DISCOVERY_NODE_RPC_URL_MAP[network_name]

    poll_interval: float = .5
    poll_timeout: float = .5
    refresh_prep_list_count: int = 60
    parallelism: int = 1


    def __init__(self, **values: Any):
        super().__init__(**values)

if __name__ == '__main__':
    c = Config()
    print(c.network_name)


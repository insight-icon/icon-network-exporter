from enum import Enum
from typing import Any
from pydantic import BaseSettings


class NetworksEnum(str, Enum):
    mainnet = 'mainnet'
    zicon = 'zicon'


class Config(BaseSettings):

    network_name: NetworksEnum = NetworksEnum.mainnet
    exporter_port: int = 6100
    exporter_address: str = ''

    main_api_endpoint: str = None
    reference_nodes: list = None
    num_data_points_retentation: int = 5

    poll_interval: float = .5
    poll_timeout: float = .5
    refresh_prep_list_count: int = 60
    parallelism: int = 1

    def __init__(self, **values: Any):
        super().__init__(**values)


if __name__ == '__main__':
    c = Config()
    print(c.network_name)


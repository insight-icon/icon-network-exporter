
discovery_node_rpc_url='https://ctz.solidwallet.io/api/v3'

request_data = {
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
                        "endRanking": "0xaaa"
                    }
                }
            }
        }

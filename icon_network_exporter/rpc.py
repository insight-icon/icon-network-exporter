def get_preps_rpc(end_ranking):
    return {
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
                    "endRanking": end_ranking
                }
            }
        }
    }

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

def get_iiss_info():
    return {
        "jsonrpc": "2.0",
        "id": 1234,
        "method": "icx_call",
        "params": {"from": "hx23ada4a4b444acf8706a6f50bbc9149be1781e13",
                   "to": "cx0000000000000000000000000000000000000000",
                   "dataType": "call",
                   "data": {"method": "getIISSInfo"}
                   }
    }

if __name__ == '__main__':
    import requests
    term_change_block = requests.post('https://ctz.solidwallet.io/api/v3',
                                      json=get_iiss_info()).json()['result']['nextCalculation']
    print()


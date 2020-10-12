def get_prep_list(prep_list):

    if not prep_list or _request_counter % 60 == 0:
        self._allpreps = (self._rpc.discovery_node_post_request()["result"]["preps"])
        self._request_counter += 1
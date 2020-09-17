from prometheus_client import start_http_server, Summary
import random
import time
import sys
import os

# Create a metric to track time spent and requests made.
# REQUEST_TIME = Summary('', '')

# print (sys.path.append(os.path.realpath(os.path.dirname(os.path.dirname(__file__)))))
print ((os.path.realpath(os.path.dirname(os.path.dirname(__file__)))))

# Decorate function with metric.
# @REQUEST_TIME.time()
def process_request(t):
    """A dummy function that takes some time."""
    time.sleep(t)


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.
    while True:
        process_request(random.random())

# from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

# class CustomCollector(object):
#     def collect(self):
#         yield GaugeMetricFamily('my_gauge', 'Help text', value=7)
#         c = CounterMetricFamily('my_counter_total', 'Help text', labels=['foo'])
#         c.add_metric(['bar'], 1.7)
#         c.add_metric(['baz'], 3.8)
#         yield c
#
# REGISTRY.register(CustomCollector())


# 2nd hellow
# from flask import Response, Flask, request
# import prometheus_client
# from prometheus_client import Summary, Counter, Histogram, Gauge
# import time
#
# app = Flask(__name__)
#
# _INF = float("inf")
#
# graphs = {}
# graphs['c'] = Counter('python_request_operations_total', 'The total number of processed requests')
# graphs['h'] = Histogram('python_request_duration_seconds', 'Histogram for the duration in seconds.',
#                         buckets=(1, 2, 5, 6, 10, _INF))
#
#
# @app.route("/")
# def hello():
#     start = time.time()
#     graphs['c'].inc()
#
#     time.sleep(0.600)
#     end = time.time()
#     graphs['h'].observe(end - start)
#     return "Hello World!"
#
#
# @app.route("/metrics")
# def requests_count():
#     res = []
#     for k, v in graphs.items():
#         res.append(prometheus_client.generate_latest(v))
#     return Response(res, mimetype="text/plain")

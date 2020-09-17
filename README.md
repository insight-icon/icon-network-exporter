## icon-network-exporter

This is a python agent that discovers nodes and extracts metrics provided through each node's REST API. Clone and run the python agent on your server and use port 6100 to get your prometheus server to scrape the metrics from this agent.

To install the icon-prometheus-exporter package.

### Manually
```bash
cd icon-prometheus-exporter
python setup.py install
```

### Docker
```bash
docker build -t insightinfrastructure/icon-network-exporter .
docker run -it insightinfrastructure/icon-network-exporter 
```

To verify
```bash
curl localhost:6100
```

## Sample Output

![GitHub Logo](https://github.com/ghalwash/icon-prometheus-exporter/blob/master/img/Screenshot.png)




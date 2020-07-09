## ICON - exporter agent for icon blockchain:
----------------

This is a python agent that discover nodes and extracts metric provided through each node's rpc. Clone and run the python agent on your server and use port 6100 to get your prometheus server to scrap the date from this agent.

To install the icon-prometheus-exporter package.

.. code-block:: bash
sudo apt-get install python-pip python-dev build-essential
sudo pip install virtualenv
sudo pip install  virtaulenvwrapper

mkdir ~/.virtualenvs

    cd icon-prometheus-exporter
    python setup.py install

you can use the [prometheus](https://github.com/ghalwash/terransible-aws-ec2-prometheus) to show the extracted data in grafana dashboards

## sample output:
----------------
![GitHub Logo](https://github.com/ghalwash/icon-prometheus-exporter/blob/master/img/Screenshot.png)





FROM python:3.8

WORKDIR /src

COPY . .

RUN python setup.py install

EXPOSE 6100
ENTRYPOINT ["icon-network-exporter"]

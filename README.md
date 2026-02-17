# vm_modem_scraper

A scraper for the Virgin Media Hub 6. Exports mostly DOCSIS stats. 

## Usage 
Build the container and set the environment variables:

```shell
docker build -t docsis_exporter:latest -f Dockerfile . 
docker run --rm -it --name vmscrape -p 8000:8000 -e GATEWAY_IP="192.168.0.1" -e LISTEN_IP="0.0.0.0" -e LISTEN_PORT=8000 docsis_exporter:latest
```

Then you can setup a scrape job in prometheus/victoria metrics:
```
  - job_name: docsis_exporter
    static_configs:
      - targets:
        - <IP_GOES_HERE>:<PORT_GOES_HERE>
```

An example Grafana Dashboard is provided in [grafana_dashboard.json](./grafana_dashboard.json)


## This is terrible
Yes - but I wrote it in an evening. PRs welcome. 

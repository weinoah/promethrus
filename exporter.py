import prometheus_client
from prometheus_client import Counter, Gauge
from prometheus_client.core import CollectorRegistry
from flask import Response, Flask
import psutil
import os
import yaml
import sys
import time

app = Flask(__name__)

REGISTRY = CollectorRegistry(auto_describe=False)
mem_rss = Gauge("system_memory_percent","process memory rss (Mb).",['prc'],registry=REGISTRY)
cpu_percent = Gauge("system_cpu_percent","process cpu percent.(%)",['prc'],registry=REGISTRY)
status = Gauge("process_up","process status",['prc'],registry=REGISTRY)

path=os.path.dirname(os.path.realpath(sys.argv[0]))
conf_file=path + '/config.yml'
conf_open = open(conf_file)
confs = yaml.load(conf_open,Loader=yaml.FullLoader).get('process')
conf_open.close()
print('===============')
print(confs)

def metric(conf):
    cmd = "ps -ef|grep "+ conf +"|grep -v grep|awk '{print $2}'"
    cmd_re=os.popen(cmd)
    pid=cmd_re.read().split('\n')[0]

    try:
        p=psutil.Process(int(pid))
        prc_cpu = p.cpu_percent()
        prc_mem = p.memory_info().rss/1024/1024
        prc_up = 1
        return {'prc_cpu':prc_cpu,'prc_mem':prc_mem,'prc_up':prc_up}
    except:
        print('no such process with pid: ' + pid)
        prc_up = 0
        return {'prc_cpu':'-1','prc_mem':'-1','prc_up':prc_up}

for conf in confs:
    print(conf)
    print(metric(conf).get('prc_mem'))

@app.route('/metrics')
def r_value():
    while True:
        for conf in confs:
            mem_rss.labels(prc=conf).set(metric(conf).get('prc_mem'))
            cpu_percent.labels(prc=conf).set(metric(conf).get('prc_cpu'))
            status.labels(prc=conf).set(metric(conf).get('prc_up'))
        return Response(prometheus_client.generate_latest(REGISTRY),mimetype="text/plain")
        time.sleep(1)

@app.route('/')
def index():
    return "Hello, Prometheus!"


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=9900,debug=True)


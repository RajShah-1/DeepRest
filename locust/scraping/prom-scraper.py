import requests
import sys
import json

PROMETHEUS_URL = "http://localhost:39963"

# Queries
EXCLUDE_INTERNAL_PODS = (
    'pod!~"elasticsearch-0|kube-.*|jaeger.*|.*prom.*|etcd.*|openebs.*"'
)

# CPU usage in minutes over the last hour
CPU_QUERY = (
    f'sum by (pod) ('
    f'  60 * rate('
    f'    container_cpu_usage_seconds_total{{{EXCLUDE_INTERNAL_PODS}}}[1m]'
    f'  )'
    f')'
)

# Memory Usage (in MB) over the last hour
MEMORY_QUERY = (
    f'sum by (pod) ('
    f'  rate('
    f'    container_memory_usage_bytes{{{EXCLUDE_INTERNAL_PODS}}}[1m]'
    f'  )'
    f')'
)


def query_prometheus_range(query, start_time, end_time, step):
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        'query': query,
        'start': start_time,
        'end': end_time,
        'step': step,
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error querying Prometheus: HTTP {response.status_code}", file=sys.stderr)
        sys.exit(1)
    data = response.json()
    if data['status'] != 'success':
        print(f"Prometheus query did not succeed: {data}", file=sys.stderr)
        sys.exit(1)
    return data['data']['result']

def main():
    import time
    end_time = int(time.time())
    start_time = end_time - 3600  # Past 1 hour
    step = "1m"  # 1-minute interval

    cpu_data = query_prometheus_range(CPU_QUERY, start_time, end_time, step)
    mem_data = query_prometheus_range(MEMORY_QUERY, start_time, end_time, step)

    result = {'cpu_usage': {}, 'memory_usage': {}}

    for item in cpu_data:
        pod = item['metric'].get('pod', 'unknown')
        result['cpu_usage'][pod] = item['values']  # List of [timestamp, value]

    for item in mem_data:
        pod = item['metric'].get('pod', 'unknown')
        result['memory_usage'][pod] = item['values']  # List of [timestamp, value]

    # Save as JSON
    with open("prometheus_data.json", "w") as json_file:
        json.dump(result, json_file, indent=4)

    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()

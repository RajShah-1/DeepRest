import requests
import sys
import json
import time
import os

PROMETHEUS_URL = "http://localhost:39963"
JAEGER_ENDPOINT = "http://localhost:34915/api/traces"
LOOKBACK = "1m"

EXCLUDE_INTERNAL_PODS = (
    'pod!~"elasticsearch-0|kube-.*|jaeger.*|.*prom.*|etcd.*|openebs.*"'
)

# Queries
CPU_QUERY = (
    f'sum by (pod) ('
    f'  60 * rate('
    f'    container_cpu_usage_seconds_total{{{EXCLUDE_INTERNAL_PODS}}}[1m]'
    f'  )'
    f')'
)

MEMORY_QUERY = (
    f'sum by (pod) ('
    f'  rate('
    f'    container_memory_usage_bytes{{{EXCLUDE_INTERNAL_PODS}}}[1m]'
    f'  )'
    f')'
)

SERVICES = [
    "sn-nginx",
    "jaeger-elasticsearch.social-network",
    "sn-social-graph-service",
    "sn-compose-post-service",
    "sn-post-storage-service",
    "sn-user-timeline-service",
    "sn-user-service",
    "sn-user-mention-service",
    "sn-home-timeline-service",
    "sn-url-shorten-service",
    "sn-write-home-timeline-service",
    "sn-media-service",
    "sn-text-service",
    "sn-unique-id-service",
]


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


def get_traces(service_name, lookback):
    url = f"{JAEGER_ENDPOINT}?service={service_name}&lookback={lookback}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch traces for {service_name}: {response.status_code}")
        return []


def main():
    end_time = int(time.time())
    start_time = end_time - 3600  # Past 1 hour
    step = 60  # 1-minute intervals

    cpu_data = query_prometheus_range(CPU_QUERY, start_time, end_time, step)
    mem_data = query_prometheus_range(MEMORY_QUERY, start_time, end_time, step)

    # Create a dictionary of timestamps
    combined_data = {}

    for item in cpu_data:
        pod = item['metric'].get('pod', 'unknown')
        for timestamp, value in item['values']:
            if timestamp not in combined_data:
                combined_data[timestamp] = {"metrics": {}, "traces": []}
            if pod not in combined_data[timestamp]["metrics"]:
                combined_data[timestamp]["metrics"][pod] = {"cpu": 0, "memory": 0}
            combined_data[timestamp]["metrics"][pod]["cpu"] += float(value)

    for item in mem_data:
        pod = item['metric'].get('pod', 'unknown')
        for timestamp, value in item['values']:
            if timestamp not in combined_data:
                combined_data[timestamp] = {"metrics": {}, "traces": []}
            if pod not in combined_data[timestamp]["metrics"]:
                combined_data[timestamp]["metrics"][pod] = {"cpu": 0, "memory": 0}
            combined_data[timestamp]["metrics"][pod]["memory"] += float(value) / (1024 * 1024)

    for svc in SERVICES:
        traces = get_traces(svc, LOOKBACK)
        if traces:
            for trace in traces.get('data', []):
                trace_start_time = int(trace.get("startTimeMillis", 0) / 1000)
                if str(trace_start_time) in combined_data:
                    combined_data[str(trace_start_time)]["traces"].append(trace)

    # Format data for final JSON output
    final_data = []
    for timestamp, data in combined_data.items():
        metrics = [{"pod": pod, "cpu": details["cpu"], "memory": details["memory"]} for pod, details in data["metrics"].items()]
        final_data.append({
            "timestamp": timestamp,
            "traces": data["traces"],
            "metrics": metrics
        })

    # Save to JSON file
    with open("merged_data.json", "w") as json_file:
        json.dump(final_data, json_file, indent=4)

    print("Merged data saved to merged_data.json")


if __name__ == "__main__":
    main()

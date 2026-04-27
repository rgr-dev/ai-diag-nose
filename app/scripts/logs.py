import os
import requests
from time import time


def dedupe_logs(logs: list[str]) -> list[str]:
    """Deduplicate log entries.

    Args:
        logs (List[str]): A list of log entries.

    Returns:
        List[str]: A deduplicated list of log entries.
    """
    seen = set()
    deduped_logs = []
    for log in logs:
        if log not in seen:
            seen.add(log)
            deduped_logs.append(log)
    return deduped_logs


def query_logs(query: str) -> list[str]:
    """Query logs from Loki.

    Args:
        query (str): The Loki query string.

    Returns:
        List[str]: A list of log entries matching the query.
    """    
    loki_url = os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/query_range")
    
    # timestamps in nanoseconds
    end = int(time() * 1e9)
    start = end - (24 * 60 * 60 * int(1e9))  # 24 hours
    params = {
        "query": query,
        "start": start,
        "end": end,
        "limit": 500
    }
    r = requests.get(
        loki_url,
        params=params)
    r.raise_for_status()

    # Extract all values lists from all result streams
    result = r.json()
    values = []
    for stream in result.get("data", {}).get("result", []):
        for entry in stream.get("values", []):
            # Remove the first element (the number), keep only the log string
            if len(entry) > 1:
                values.append(entry[1])
    if values:
        return dedupe_logs(values)
    return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query logs from Loki.")
    parser.add_argument("query", type=str, help="Loki query string")
    args = parser.parse_args()

    result = query_logs(args.query)
    import json
    print(json.dumps(result, indent=2))
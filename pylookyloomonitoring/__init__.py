from __future__ import annotations

import argparse
import json
import sys

from typing import Any

from .api import PyLookylooMonitoring, CaptureSettings  # noqa

__all__ = [
    'PyLookylooMonitoring',
    'CaptureSettings'
]


def main() -> None:
    parser = argparse.ArgumentParser(description='Talk to a Lookyloo Monitoring instance.')
    parser.add_argument('--url', type=str, required=True, help='URL of the instance.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--monitor_url', type=str, help='URL to monitor. It will be monitered hourly.')
    group.add_argument('--compare', type=str, help='UUID of the monitoring.')
    args = parser.parse_args()

    client = PyLookylooMonitoring(args.url)

    response: str | dict[str, Any]
    if not client.is_up:
        print(f'Unable to reach {client.root_url}. Is the server up?')
        sys.exit(1)
    if args.monitor_url:
        response = client.monitor({'url': args.monitor_url, 'listing': False}, frequency='hourly')
    else:
        response = client.changes(args.compare)
    print(json.dumps(response, indent=2))

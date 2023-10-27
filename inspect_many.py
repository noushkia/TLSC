import configparser
import argparse
from enum import Enum
from multiprocessing import cpu_count
from pathlib import Path

from inspector.controller import run_inspectors, InspectorType

import pandas as pd
import numpy as np

config = configparser.ConfigParser()
config.read('config.ini')

# rpc ips file path
rpc_hosts_ip_path = config['paths']["rpc_hosts_ip_path"]

# load log paths
logs_path = Path(config["logs"]["logs_path"])
inspectors_log_path = logs_path / config["logs"]["inspectors_log_path"]


def create_dirs(*dirs):
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def get_rpc_endpoints(endpoint_ip_file_path):
    return pd.read_csv(endpoint_ip_file_path, names=["ip"])


if __name__ == "__main__":
    create_dirs(logs_path, inspectors_log_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--after', type=int, help='Block number to start from', default=0)
    parser.add_argument('-b', '--before', type=int, help='Block number to end with', default=1)
    parser.add_argument('-p', '--para', type=int, help='Maximum number of parallel processes/inspectors',
                        default=cpu_count())

    parser.add_argument('-mc', '--many-contracts', action='store_true',
                        help='Inspect collected contracts in given range', default=None)

    parser.add_argument('-mb', '--many-blocks', action='store_true', help='Inspect many blocks in given range',
                        default=None)
    args = parser.parse_args()

    if args.after >= args.before:
        raise ValueError("After block number must be smaller than before block number")
    elif args.after < 0 or args.before < 0:
        raise ValueError("Block number must be positive")
    elif args.para <= 0:
        raise ValueError("Number of parallel processes must be positive")

    inspector_cnt = args.para
    rpc_urls = get_rpc_endpoints(rpc_hosts_ip_path)

    if args.after != 0:
        task_batches = np.linspace(start=args.after, stop=args.before, num=inspector_cnt + 1)
        inspector_type = InspectorType.TLSC
        if args.many_contracts is True:
            inspector_type = InspectorType.CONTRACT
        elif args.many_blocks is True:
            inspector_type = InspectorType.BLOCK
    else:
        raise ValueError("Invalid arguments")

    run_inspectors(task_batches, rpc_urls, inspector_cnt, inspector_type=inspector_type)

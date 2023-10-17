import configparser
import argparse
from multiprocessing import cpu_count
from pathlib import Path

import pandas as pd
import numpy as np

from tlsc_inspector.inspectors import run_inspectors

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
    parser.add_argument('-a', '--after', type=int, help='Block number to start from')
    parser.add_argument('-b', '--before', type=int, help='Block number to end with')
    parser.add_argument('-p', '--para', type=int, help='Maximum number of parallel processes/inspectors',
                        default=cpu_count())
    args = parser.parse_args()

    inspector_cnt = args.para
    block_batches = np.linspace(start=args.after, stop=args.before, num=inspector_cnt + 1)
    rpc_urls = get_rpc_endpoints(rpc_hosts_ip_path)
    run_inspectors(block_batches, rpc_urls, inspector_cnt)

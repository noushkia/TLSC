import logging
import sys
from multiprocessing import Pool

import pandas as pd
import requests
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
PING_CNT = 10
SESSION = requests.Session()

client = "erigon"


def check_host(ip_address: str) -> float:
    """
    Checks the latency of the specified host by sending an RPC request to it.

    Args:
        ip_address (str): The IP address of the host to check.

    Returns:
        float: The latency of the host in microseconds, or -1 if the host is unresponsive.
    """
    logger.info(f"{ip_address}: GET")

    try:
        response_times = []
        for _ in range(PING_CNT):
            r = SESSION.get(
                f"http://{ip_address}:8545/",
                timeout=2,
                json={
                    "method": "trace_block",
                    "params": [15500000],
                    "id": 1,
                    "jsonrpc": "2.0"
                },
                headers={'Content-type': 'application/json'}
            )
            if 'error' in r.json():
                logger.info(f"{ip_address}: RPC Error")
                return -1
            response_times.append(r.elapsed.microseconds)
        avg_latency = sum(response_times) / len(response_times)
        logger.info(f"{ip_address}: Success")
        return avg_latency

    except ConnectTimeout:
        logger.info(f"{ip_address}: Connect Timeout")
        return -1
    except ConnectionError:
        logger.info(f"{ip_address}: Connect Error")
        return -1
    except ReadTimeout:
        logger.info(f"{ip_address}: Read Timeout")
        return -1
    except Exception:
        logger.info(f"{ip_address}: Unknown Error")
        return -1


if __name__ == "__main__":
    logger.info("Collecting hosts")
    hosts = pd.read_csv(f"{client}_hosts.csv", names=["ip_address"], usecols=[0])

    logger.info("Sorting hosts")
    with Pool() as p:
        hosts["avg_latency"] = p.map(check_host, hosts["ip_address"])

    # remove unresponsive nodes
    hosts.drop(hosts[hosts['avg_latency'] == -1].index, inplace=True)

    # sort node addresses by response time
    hosts.sort_values(by=["avg_latency"], inplace=True)

    hosts.drop(columns=["avg_latency"], inplace=True)

    logger.info("Writing to file")
    with open(f"{client}_sorted_hosts.csv", "w") as f:
        hosts.to_csv(f, index=False, header=False)

    logger.info("Done")

import configparser
from enum import Enum
from multiprocessing import Pool
import traceback
import asyncio
import logging
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd

from inspector.inspectors.block.block import BlockInspector
from inspector.inspectors.tlsc.tlsc import TLSCInspector
from inspector.inspectors.contract.contract import ContractInspector
from inspector.utils import get_log_handler, clean_up_log_handlers
from inspector.verified_contracts import inspect_verified_contracts
from utils.db import get_inspect_session, create_tables

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logs_path = Path(config['logs']['logs_path']) / "inspectors.log"

formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

ETHERSCAN_API_KEYS = [
    "W371NBK6V9SAB8ETM3VFEIM93AJUQDZJGI",
    "I3T9RMRZVVQQ3U93VWKD46Q6IJ6YMYC8KY",
    "T48DJNQHTTC6TGKR4ZW19ZSBR9XH17R5S3",
    "83BARI76JCM3WT4MTPQA2FEBCMA5IGI8PI",
    "PUR8QWEWKF6IQVH64SA4FSP1Y492N3TEEC",
    "59VJZWW7UY6TXDNCDRYJ3X6RAKKD8IMR5D",
    "NV1VNKU47AUBGK9CRMK6A1P1E4PDCUH2ZZ",
    "BC8H4KH7AKSXTWWFVYK4HSYM8JFHIXYNCS",
    "DQEFKSEBAS5H86I5K77ZXN81GJXFSDTSCG",
]


class InspectorType(Enum):
    BLOCK = "block"
    CONTRACT = "contract"
    TLSC = "tlsc"
    VERICON = "verified"


def inspect_many(
        index: int,
        task_batch,
        inspector_type: InspectorType,
        rpc: str,
        attributes: List[str] = None,
        max_concurrency: int = 1,
        request_timeout: int = 500,
):
    inspect_db_session = get_inspect_session()
    tasks = (task_batch[0], task_batch[1])

    if inspector_type == InspectorType.BLOCK:
        inspector = BlockInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
            etherscan_api_key=ETHERSCAN_API_KEYS[index % len(ETHERSCAN_API_KEYS)],
            attributes=attributes,
        )
        logger.info(f"Starting up block inspector {rpc} for blocks {task_batch[0]} to {task_batch[1]}")
    elif inspector_type == InspectorType.CONTRACT:
        inspector = ContractInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
        )
        logger.info(f"Starting up contracts inspector {rpc} created in blocks {task_batch[0]} to {task_batch[1]}")
    elif inspector_type == InspectorType.TLSC:
        inspector = TLSCInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
        )
        logger.info(f"Starting up tlsc inspector {rpc} for blocks {task_batch[0]} to {task_batch[1]}")
    elif inspector_type == InspectorType.VERICON:
        inspect_verified_contracts(inspect_db_session,
                                   tasks,
                                   ETHERSCAN_API_KEYS[index % len(ETHERSCAN_API_KEYS)]
                                   )
        return
    else:
        raise ValueError(f"Invalid inspector type {inspector_type}")

    try:
        asyncio.run(inspector.inspect_many(
            task_batch=tasks,
            inspect_db_session=inspect_db_session,
        ), debug=False)
    except Exception as e:
        logger.error(f"Process {index} exited due to {type(e)}:\n{traceback.format_exc()}")


def run_inspectors(
        task_batches: np.ndarray[Tuple[int, int]],
        rpc_urls: pd.DataFrame,
        inspector_cnt: int,
        inspector_type: InspectorType = InspectorType.TLSC,
        attributes: List[str] = None,
) -> None:
    log_file_handler = get_log_handler(logs_path, formatter, rotate=False)
    logger.addHandler(log_file_handler)

    if inspector_cnt > len(rpc_urls):
        logger.warning(f"Number of inspectors ({inspector_cnt}) exceeds number of RPC URLs ({len(rpc_urls)}).")

    create_tables()

    rpc_inputs = [
        (
            i,  # inspectors index
            (int(task_batches[i]), int(task_batches[i + 1])),  # (after_block, before_block)
            f"http://{rpc_urls.ip[i % len(rpc_urls)]}:8545/",  # rpc
            attributes,  # attributes
            # 4,                                               # max_concurrency
        )
        for i in range(inspector_cnt)
    ]

    with Pool(processes=inspector_cnt) as pool:
        processes = [pool.apply_async(inspect_many, args=(_input[0], _input[1], inspector_type, _input[2], _input[3]))
                     for _input in rpc_inputs]

        for process in processes:
            try:
                process.get()
            except Exception as e:
                logger.error(f"Process exited due to {type(e)}:\n{traceback.format_exc()}")

    logger.info("All inspectors finished")
    clean_up_log_handlers(logger)

import configparser
from enum import Enum
from multiprocessing import Pool
import traceback
import asyncio
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from inspector.inspectors.block.block import BlockInspector
from inspector.inspectors.tlsc.tlsc import TLSCInspector
from inspector.inspectors.contract.contract import ContractInspector
from inspector.utils import get_log_handler, clean_up_log_handlers
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


class InspectorType(Enum):
    BLOCK = "block"
    CONTRACT = "contract"
    TLSC = "tlsc"


def inspect_many(
        index: int,
        task_batch,
        inspector_type: InspectorType,
        rpc: str,
        max_concurrency: int = 1,
        request_timeout: int = 500,
):
    inspect_db_session = get_inspect_session()

    if inspector_type == InspectorType.BLOCK:
        inspector = BlockInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
        )
        args = (task_batch[0], task_batch[1])
        logger.info(f"Starting up block inspector {rpc} for blocks {task_batch[0]} to {task_batch[1]}")
    elif inspector_type == InspectorType.CONTRACT:
        inspector = ContractInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
        )
        args = task_batch
        logger.info(f"Starting up contract inspector {rpc} for {len(task_batch)} contracts")
    elif inspector_type == InspectorType.TLSC:
        inspector = TLSCInspector(
            rpc,
            max_concurrency=max_concurrency,
            request_timeout=request_timeout,
        )
        args = (task_batch[0], task_batch[1])
        logger.info(f"Starting up tlsc inspector {rpc} for blocks {task_batch[0]} to {task_batch[1]}")
    else:
        raise ValueError(f"Invalid inspector type {inspector_type}")

    try:
        asyncio.run(inspector.inspect_many(
            task_batch=args,
            inspect_db_session=inspect_db_session,
        ), debug=False)
    except Exception as e:
        logger.error(f"Process {index} exited due to {type(e)}:\n{traceback.format_exc()}")


def run_inspectors(
        task_batches: np.ndarray[Tuple[int, int]] | List[List[Tuple[int, str]]],
        rpc_urls: pd.DataFrame,
        inspector_cnt: int,
        inspector_type: InspectorType = InspectorType.TLSC,
) -> None:
    log_file_handler = get_log_handler(logs_path, formatter, rotate=False)
    logger.addHandler(log_file_handler)

    if inspector_cnt > len(rpc_urls):
        logger.warning(f"Number of inspectors ({inspector_cnt}) exceeds number of RPC URLs ({len(rpc_urls)}).")

    create_tables()

    if inspector_type == InspectorType.CONTRACT:
        rpc_inputs = [
            (
                i,  # inspectors index
                task_batches[i],  # contract_addresses
                f"http://{rpc_urls.ip[i % len(rpc_urls)]}:8545/"  # rpc
                # 4,                                # max_concurrency
            )
            for i in range(inspector_cnt)
        ]
    elif inspector_type == InspectorType.TLSC or inspector_type == InspectorType.BLOCK:
        rpc_inputs = [
            (
                i,  # inspectors index
                (int(task_batches[i]), int(task_batches[i + 1])),  # (after_block, before_block)
                f"http://{rpc_urls.ip[i % len(rpc_urls)]}:8545/"  # rpc
                # 4,                                # max_concurrency
            )
            for i in range(inspector_cnt)
        ]
    else:
        raise ValueError(f"Invalid inspector type {inspector_type}")

    with Pool(processes=inspector_cnt) as pool:
        processes = [pool.apply_async(inspect_many, args=(_input[0], _input[1], inspector_type, _input[2])) for _input
                     in rpc_inputs]

        for process in processes:
            try:
                process.get()
            except Exception as e:
                logger.error(f"Process exited due to {type(e)}:\n{traceback.format_exc()}")

    logger.info("All inspectors finished")
    clean_up_log_handlers(logger)

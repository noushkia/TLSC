import configparser
from multiprocessing import Pool
import traceback
import asyncio
import logging
from pathlib import Path

from utils.db import get_inspect_session, create_tables
from tlsc_inspector.utils import get_handler
from tlsc_inspector.inspector import TLSCInspector

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


def _inspect_many_blocks(
        index: int,
        after_block: int,
        before_block: int,
        rpc: str,
        max_concurrency: int = 1,
        request_timeout: int = 500,
):
    logger.info(f"Starting up inspector {rpc} for blocks {after_block} to {before_block}")
    inspect_db_session = get_inspect_session()

    inspector = TLSCInspector(
        rpc,
        max_concurrency=max_concurrency,
        request_timeout=request_timeout,
    )

    try:
        asyncio.run(inspector.inspect_many_blocks(
            after_block=after_block,
            before_block=before_block,
            inspect_db_session=inspect_db_session,
        ), debug=False)
    except Exception as e:
        logger.error(f"Process {index} exited due to {type(e)}:\n{traceback.format_exc()}")


def run_inspectors(block_intervals, rpc_urls, inspector_cnt):
    logger.addHandler(get_handler(logs_path, formatter, rotate=False))

    if inspector_cnt > len(rpc_urls):
        logger.warning(f"Number of inspectors ({inspector_cnt}) exceeds number of RPC URLs ({len(rpc_urls)}).")

    create_tables()

    rpc_inputs = [
        (
            i,  # inspector index
            int(block_intervals[i]),  # after_block
            int(block_intervals[i + 1]),  # before_block
            f"http://{rpc_urls.ip[i % len(rpc_urls)]}:8545/"  # rpc
            # 4,                                # max_concurrency
        )
        for i in range(inspector_cnt)
    ]

    with Pool(processes=inspector_cnt) as pool:
        processes = [pool.apply_async(_inspect_many_blocks, args=_input) for _input in rpc_inputs]
        for process in processes:
            try:
                process.get()
            except Exception as e:
                logger.error(f"Process exited due to {type(e)}:\n{traceback.format_exc()}")

import logging
import multiprocessing
import traceback
from typing import List, Tuple, Dict

from code_analyzer.time_lock.time_lock_detector import bytecode_has_time_lock

BATCH_SIZE = 2


def _setup_console_handler() -> logging.Handler:
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    return console_handler


def analyze_bytecodes(analyzer_idx: int, contracts: List[Tuple[str, str]]) -> None:
    """
    Analyze the bytecodes for time locks and stores the addresses of time-locked contracts in a csv file.
    :param analyzer_idx: The number of the analyzer process.
    :param contracts: Array of bytecodes and their respective addresses to analyze.
    :return: None
    """
    tlsc: Dict[str, bool] = dict()
    logger = logging.getLogger(f"analyzer_{analyzer_idx}")

    logger.setLevel(logging.INFO)
    logger.addHandler(_setup_console_handler())

    try:
        tlsc.clear()
        batch_cnt = 0
        for address, bytecode in contracts:
            batch_cnt += 1
            logger.info(f"{analyzer_idx}: Analyzing {address}")
            tlsc[address] = bytecode_has_time_lock(bytecode)
            if batch_cnt % BATCH_SIZE == 0:
                with open(f"tlsc_{analyzer_idx}.csv", "a") as f:
                    for contract_address, has_tl in tlsc.items():
                        f.write(f"{contract_address},{has_tl}\n")
                tlsc.clear()
    except:
        logger.error(f"Error in analyzer {analyzer_idx}:\n{traceback.format_exc()}")
    finally:
        with open(f"tlsc_{analyzer_idx}.csv", "a") as f:
            for address, has_tl in tlsc.items():
                f.write(f"{address},{has_tl}\n")


def parallel_analysis(contracts: List[Tuple[str, str]], analyzer_cnt: int = 8):
    """
    Analyze the bytecodes in parallel.
    :return: Array of bytecode addresses that have time locks.
    """
    chunk_size = len(contracts) // analyzer_cnt
    contracts_batches = []
    for i in range(0, len(contracts), chunk_size):
        contracts_batches.append(contracts[i:i + chunk_size])
    with multiprocessing.Pool(processes=analyzer_cnt) as pool:
        processes = [pool.apply_async(analyze_bytecodes, args=(i, contracts_batches[i])) for i in range(analyzer_cnt)]

        for process in processes:
            try:
                process.get()
            except Exception as e:
                print(f"Process exited due to {type(e)}:\n{traceback.format_exc()}")

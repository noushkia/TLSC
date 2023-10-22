import configparser
import logging
from pathlib import Path
from typing import List, Dict

from sqlalchemy import orm
from web3 import Web3

from analyzer.time_lock_detector import bytecode_has_potential_time_lock
from inspector.models.contract.model import Contract
from inspector.models.crud import insert_data
from inspector.utils import get_log_handler, clean_up_log_handlers

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


async def _fetch_block_transactions(w3, block_number: int) -> List:
    block_json = await w3.eth.get_block(block_identifier=block_number, full_transactions=True)
    return block_json["transactions"]


async def _fetch_contract_code(w3, contract_address: str, block_number: int) -> str:
    return await w3.eth.get_code(account=contract_address, block_identifier=block_number)


async def inspect_many_blocks(
        web3: Web3,
        after_block_number: int,
        before_block_number: int,
        host: str,
        inspect_db_session: orm.Session,
) -> None:
    """
    Inspects blocks for time lock smart contracts.
    Fetches the contract code from their initial transaction and checks if it has a potential time lock.

    :param web3: Web3 provider
    :param after_block_number: Block number to start from
    :param before_block_number: Block number to end with
    :param host: RPC endpoint url
    :param inspect_db_session: DB session
    :return: None
    """
    logs_path = Path(config['logs']['logs_path']) / config['logs']['inspectors_log_path'] / f"inspector_{host}.log"
    log_file_handler = get_log_handler(logs_path, formatter, rotate=True)
    logger.addHandler(log_file_handler)

    all_tlscs: List[Dict] = []

    logger.info(f"Inspecting blocks {after_block_number} to {before_block_number}")
    for block_number in range(after_block_number, before_block_number):
        logger.debug(f"Block: {block_number} -- Getting block data")

        block_transactions = await _fetch_block_transactions(web3, block_number)

        for tx in block_transactions:
            # else, check if it's from an already known contract
            if tx['to'] is None:
                receipt = await web3.eth.get_transaction_receipt(tx['hash'])
                contract_address = receipt['contractAddress']
                bytecode = await _fetch_contract_code(web3, contract_address, block_number)
                bytecode = bytecode.hex()
                # Ignore empty bytecodes
                if bytecode == "0x":
                    continue

                logger.debug(f"Block: {block_number} -- Contract: {contract_address} -- Check TL")

                if not bytecode_has_potential_time_lock(bytecode):
                    continue

                logger.debug(f"Block: {block_number} -- Contract: {contract_address} -- Append tlscs")

                all_tlscs.append({
                    "contract_address": contract_address,
                    "bytecode": bytecode,
                    "from_address": tx['from'],
                    "tx_hash": tx['hash'].hex(),
                    "block_number": block_number,
                })

    if all_tlscs:
        logger.debug("Writing to DB")
        insert_data(Contract, all_tlscs, inspect_db_session)
        logger.debug("Writing done")

    clean_up_log_handlers(logger)

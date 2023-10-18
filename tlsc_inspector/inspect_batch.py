import configparser
import logging
from pathlib import Path
from typing import List

from eth_utils import to_checksum_address
from sqlalchemy import orm
from web3 import Web3

from tlsc_inspector.analyzer.time_lock_detector import check_bytecode_time_lock
from tlsc_inspector.contract.crud import write_contracts
from tlsc_inspector.contract.model import Contract
from tlsc_inspector.utils import get_handler

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
    block_json = await w3.eth.get_block(block_identifier=block_number, full_transactions=False)
    return block_json["transactions"]


async def _fetch_contract_code(w3, contract_address: str, block_number: int) -> str:
    return await w3.eth.get_code(account=contract_address, block_identifier=block_number)


# Todo: get contract balance
def get_contract_eth_balance(w3, contract_address):
    checksum_address = to_checksum_address(contract_address)
    balance_in_wei = w3.eth.getBalance(checksum_address)
    balance_in_eth = w3.fromWei(balance_in_wei, 'ether')
    return balance_in_eth


async def inspect_many_blocks(
        web3: Web3,
        after_block_number: int,
        before_block_number: int,
        host: str,
        inspect_db_session: orm.Session,
):
    logs_path = Path(config['logs']['logs_path']) / config['logs']['inspectors_log_path'] / f"inspector_{host}.log"
    logger.addHandler(get_handler(logs_path, formatter, rotate=True))

    all_tlscs: List[Contract] = []

    logger.info(f"Inspecting blocks {after_block_number} to {before_block_number}")
    for block_number in range(after_block_number, before_block_number):
        logger.debug(f"Block: {block_number} -- Getting block data")

        block_transactions = await _fetch_block_transactions(web3, block_number)

        for tx_hash in block_transactions:
            tx = await web3.eth.get_transaction(tx_hash)

            if tx['to'] is None:
                receipt = await web3.eth.get_transaction_receipt(tx_hash)
                contract_address = receipt['contractAddress']
                bytecode = await _fetch_contract_code(web3, contract_address, block_number)
                bytecode = bytecode.hex()
                # Ignore empty bytecodes
                if bytecode == "0x":
                    continue

                if not check_bytecode_time_lock(bytecode):
                    continue

                all_tlscs.append(Contract(
                    contract_address=contract_address,
                    bytecode=bytecode,
                    from_address=tx['from'],
                    tx_hash=tx['hash'],
                    block_number=block_number
                ))

    logger.debug("Writing to DB")
    write_contracts(all_tlscs, inspect_db_session)
    logger.debug("Writing done")

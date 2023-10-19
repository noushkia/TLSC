import configparser
import logging
from pathlib import Path
from typing import List

from sqlalchemy import orm
from web3 import Web3

from inspector.models.contract_info.crud import write_contracts_info
from inspector.models.contract_info.model import ContractInfo
from inspector.utils import get_log_handler

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

OLDEST_BLOCK = 15649595  # first block on October 2022


async def _fetch_contract_tx_count(w3, contract_address: str) -> int:
    return await w3.eth.get_transaction_count(contract_address, block_identifier=OLDEST_BLOCK)


async def _fetch_latest_contract_transactions(w3, contract_address: str) -> List:
    return []


async def _fetch_contract_eth_balance(w3, contract_address: str) -> float:
    return 0


async def inspect_many_contracts(
        web3: Web3,
        contracts: List[str],
        host: str,
        inspect_db_session: orm.Session,
):
    logs_path = Path(config['logs']['logs_path']) / config['logs']['inspectors_log_path'] / f"inspector_{host}.log"
    logger.addHandler(get_log_handler(logs_path, formatter, rotate=True))

    # largest tx hash, largest tx value, largest tx block number, contract ETH balance
    all_info: List[ContractInfo] = []

    logger.info(f"{host}: Inspecting {len(contracts)} contracts")
    for contract_address in contracts:
        logger.debug(f"Contract: {contract_address} -- Getting contract data")

        latest_tx_cnt = await _fetch_contract_tx_count(web3, contract_address)

        if latest_tx_cnt == 0:
            continue

    contract_transactions = await _fetch_latest_contract_transactions(web3, contract_address)
    contract_balance = await _fetch_contract_eth_balance(web3, contract_address)
    largest_tx_value = 0

    for tx_hash in contract_transactions:
        # get the largest transaction for each contract
        tx = await web3.eth.get_transaction(tx_hash)

        # get the largest transaction value
        if tx['value'] > largest_tx_value:
            largest_tx_value = tx['value']
            largest_tx_value_hash = tx_hash
            largest_tx_value_block_number = tx['blockNumber']

            all_info.append(
                ContractInfo(
                    address=contract_address,
                    largest_tx_hash=largest_tx_value_hash,
                    largest_tx_value=largest_tx_value,
                    largest_tx_block_number=largest_tx_value_block_number,
                    eth_balance=contract_balance,
                )
            )

    logger.debug("Writing to DB")
    print(all_info)
    # write_contracts_info(all_info, inspect_db_session)
    logger.debug("Writing done")

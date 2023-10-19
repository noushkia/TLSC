import configparser
import logging
from pathlib import Path
from typing import List

from sqlalchemy import orm
from web3 import Web3, exceptions

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
ETH_TO_WEI = 1e18


async def _fetch_contract_tx_count(w3, contract_address: str) -> int:
    checksum_contract_address = Web3.to_checksum_address(contract_address)
    return await w3.eth.get_transaction_count(checksum_contract_address, block_identifier=OLDEST_BLOCK)


async def _fetch_latest_contract_transactions(w3, contract_address: str, latest_tx_cnt: int) -> List:
    checksum_contract_address = Web3.to_checksum_address(contract_address)

    # todo: Iterate over all blocks and get the transactions based on address values
    #  I suggest you do this in the block inspector so that it gets miner revenue and all the other stuff
    filter_params = {
        'address': checksum_contract_address,
        'fromBlock': OLDEST_BLOCK,
        'toBlock': 'latest',
    }

    # Retrieve the latest transactions matching the filter
    logs = await w3.eth.get_logs(filter_params)
    latest_logs = logs[-latest_tx_cnt:]

    latest_transactions = [log['transactionHash'] for log in latest_logs]

    return latest_transactions


async def _fetch_contract_eth_balance(w3, contract_address: str) -> float:
    checksum_contract_address = Web3.to_checksum_address(contract_address)

    return await w3.eth.get_balance(checksum_contract_address) / ETH_TO_WEI


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

        try:
            latest_tx_cnt = await _fetch_contract_tx_count(web3, contract_address)
        except exceptions.InvalidAddress:
            logger.error(f"Contract: {contract_address} -- Invalid address")
            raise exceptions.InvalidAddress

        if latest_tx_cnt == 0:
            continue

        contract_transactions = await _fetch_latest_contract_transactions(web3, contract_address, latest_tx_cnt)
        contract_balance = await _fetch_contract_eth_balance(web3, contract_address)
        largest_tx_value = -1

        logger.info(f"Contract: {contract_address} -- Found {len(contract_transactions)} transactions")
        logger.info(f"Contract: {contract_address} -- Balance: {contract_balance} ETH")

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
                        contract_address=contract_address,
                        largest_tx_hash=largest_tx_value_hash.hex(),
                        largest_tx_value=largest_tx_value,
                        largest_tx_block_number=largest_tx_value_block_number,
                        eth_balance=contract_balance,
                    )
                )

    logger.debug("Writing to DB")
    write_contracts_info(all_info, inspect_db_session)
    logger.debug("Writing done")

from logging import Logger
from typing import List, Dict

from sqlalchemy import orm
from web3 import Web3

from inspector.models.contract_info.model import ContractInfo
from inspector.models.crud import insert_data

OLDEST_BLOCK = 15649595  # first block on October 2022
ETH_TO_WEI = 1e18


async def _fetch_contract_tx_count(w3, contract_address: str) -> int:
    checksum_contract_address = Web3.to_checksum_address(contract_address)
    return await w3.eth.get_transaction_count(checksum_contract_address, block_identifier=OLDEST_BLOCK)


async def _fetch_contract_eth_balance(w3, contract_address: str) -> float:
    checksum_contract_address = Web3.to_checksum_address(contract_address)

    return await w3.eth.get_balance(checksum_contract_address) / ETH_TO_WEI


async def inspect_many_contracts(
        web3: Web3,
        contracts: List[str],
        logger: Logger,
        inspect_db_session: orm.Session,
):
    # largest tx hash, largest tx value, largest tx block number, contract ETH balance
    all_info: List[Dict] = []

    logger.info(f"Inspecting contracts {contracts[0][0]} to {contracts[-1][0]}")
    for index, contract_address in contracts:
        logger.debug(f"Contract: {contract_address} -- Getting contract data")

        contract_balance = await _fetch_contract_eth_balance(web3, contract_address)

        if contract_balance == 0:
            continue

        # the block inspector will fetch the info related to the transactions
        all_info.append({
            "contract_address": contract_address,
            "eth_balance": contract_balance,
            "largest_tx_hash": None,
            "largest_tx_block_number": None,
            "largest_tx_value": None,
        })

    if all_info:
        logger.debug("Writing to DB")
        insert_data(ContractInfo, all_info, inspect_db_session)
        logger.debug("Writing done")

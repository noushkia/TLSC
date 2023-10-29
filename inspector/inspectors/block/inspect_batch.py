import asyncio
from typing import List, Tuple, Dict

import aiohttp
from aiohttp import ClientSession
from sqlalchemy import orm, select
from web3 import Web3

from inspector.models.block.model import Block
from inspector.models.contract_info.model import ContractInfo
from inspector.models.crud import insert_data, update_data
from inspector.utils import configure_logger, clean_up_log_handlers

ETH_TO_WEI = 1e18


async def _fetch_block_info(w3: Web3, block_number: int) -> Tuple[str, int, int, List]:
    """
    Fetches block info from web3.

    :param w3: Web3 provider
    :param block_number: Block number to fetch
    :return: Tuple of miner address, gas used, gas limit, transactions
    """
    # need to fetch gasUsed for each transaction, which is not in this response
    block_info = await w3.eth.get_block(block_number, full_transactions=True)
    return block_info['miner'], block_info['gasUsed'], block_info['gasLimit'], block_info['transactions']


# https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.fee_history
async def _fetch_base_fees_per_gas(
        w3: Web3,
        block_count: int,
        newest_block_number: int
) -> List[int]:
    base_fees = await w3.eth.fee_history(block_count, newest_block_number, [2, 98])
    base_fees_per_gas = base_fees["baseFeePerGas"]
    if len(base_fees_per_gas) == 0:
        raise RuntimeError("Unexpected error - no fees returned")
    return base_fees_per_gas


async def _fetch_etherscan_data(
        session: ClientSession,
        url: str
) -> Dict:
    # Fetch etherscan data asynchronously
    async with session.get(url) as response:
        data = await response.json()
        return data


async def inspect_many_blocks(
        web3: Web3,
        after_block_number: int,
        before_block_number: int,
        host: str,
        inspect_db_session: orm.Session,
        etherscan_block_reward_url: str = None,
) -> None:
    """
    Inspects many blocks and writes them to DB.
    Fetches the miner revenue from block rewards and fees. (todo: MEV)
    Fetches the transactions that are from/to time-locked contracts. (todo: ERC20 tokens)
    :param etherscan_block_reward_url: Etherscan API url for getting the block rewards
    :param web3: Web3 provider
    :param after_block_number: Block number to start from
    :param before_block_number: Block number to end with
    :param host: RPC endpoint url
    :param inspect_db_session: DB session
    :return: None
    """
    # todo: configure one for the inspector and not each function
    logger = configure_logger(host)

    all_blocks: List[Dict] = []
    all_updated_info: List[Dict] = []

    # get the addresses of all contracts and convert them to map of address to value
    sc_query_response = inspect_db_session.execute(
        select(ContractInfo.contract_address, ContractInfo.largest_tx_value)).all()
    smart_contracts = {contract_address: largest_tx_value for contract_address, largest_tx_value in sc_query_response}

    logger.info(f"Inspecting blocks {after_block_number} to {before_block_number}")

    base_fees_per_gas = await _fetch_base_fees_per_gas(web3,
                                                       before_block_number - after_block_number,
                                                       before_block_number - 1)

    i = 0
    for block_number in range(after_block_number, before_block_number):
        logger.debug(f"Block: {block_number} -- Getting block data")
        async with aiohttp.ClientSession() as session:
            tasks = [
                _fetch_block_info(web3, block_number),
                _fetch_etherscan_data(session, etherscan_block_reward_url.format(block_number))
            ]
            block_info, etherscan_response = await asyncio.gather(*tasks)
        miner_address, total_gas_used, block_gas_limit, block_transactions = block_info
        block_reward = float(etherscan_response['result']['blockReward']) / ETH_TO_WEI

        # check if it's from or to an already known contract
        batch_updated_info, coinbase_transfer = check_block_transactions(block_transactions, smart_contracts,
                                                                         miner_address, block_number)
        all_updated_info.extend(batch_updated_info)
        all_blocks.append({
            "block_number": block_number,
            "miner_address": miner_address,
            "coinbase_transfer": coinbase_transfer,
            "base_fee_per_gas": base_fees_per_gas[i] / ETH_TO_WEI,
            "gas_fee": block_reward,  # miner_fee = transactions_fee - burnt_fee (EIP-1559)
            "gas_used": total_gas_used,
            "gas_limit": block_gas_limit,
        })

        i += 1

    # todo: return these lists and use the database in the inspector level?
    if all_blocks:
        logger.debug("Writing to DB")
        insert_data(Block, all_blocks, inspect_db_session)
        logger.debug("Writing done")

    if all_updated_info:
        logger.debug("Updating DB")
        update_data(ContractInfo, all_updated_info, inspect_db_session)
        logger.debug("Updating done")

    clean_up_log_handlers(logger)


def check_block_transactions(
        block_transactions: List,
        smart_contracts: Dict,
        miner_address: str,
        block_number: int
) -> Tuple[List, float]:
    """
    Checks the transactions of a block for time-locked contracts transactions and coinbase transfers.
    :param block_transactions: List of transactions in the block
    :param smart_contracts: Map of time-locked contracts addresses to their largest transaction value
    :param miner_address: The address of the miner of the block
    :param block_number: The block number
    :return: Tuple of list of time-locked contracts transactions and coinbase transfer
    """
    coinbase_transfer = 0
    larger_contracts_transactions = []
    for tx in block_transactions:
        to_address = tx['to']
        from_address = tx['from']
        transaction_value = float(tx['value']) / ETH_TO_WEI
        contract_address = None
        if smart_contracts.get(to_address) is not None:
            contract_address = to_address
        elif smart_contracts.get(from_address) is not None:
            contract_address = from_address
        # TODO: must update DB with new largest tx values. This is a shared resource and must be locked.
        if contract_address is not None and smart_contracts[contract_address] < transaction_value:
            larger_contracts_transactions.append({
                "contract_address": contract_address,
                "largest_tx_hash": tx['hash'].hex(),
                "largest_tx_block_number": block_number,
                "largest_tx_value": transaction_value,
            })
            smart_contracts[contract_address] = transaction_value

        if to_address == miner_address:
            coinbase_transfer += transaction_value

    return larger_contracts_transactions, coinbase_transfer

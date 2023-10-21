import configparser
import logging
from pathlib import Path
from typing import List, Tuple, Dict

from sqlalchemy import orm, select
from web3 import Web3

from inspector.models.block.model import Block
from inspector.models.contract_info.model import ContractInfo
from inspector.models.crud import insert_data, update_data
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


async def _fetch_block_info(w3: Web3, block_number: int) -> Tuple[str, int, int, List[Dict[str, str]]]:
    """
    Fetches block info from web3.

    :param w3: Web3 provider
    :param block_number: Block number to fetch
    :return: Tuple of miner address, gas used, gas limit, transactions
    """
    block_info = await w3.eth.get_block(block_number)
    return block_info['miner'], block_info['gasUsed'], block_info['gasLimit'], block_info['transactions']


# https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.fee_history
async def _fetch_base_fees_per_gas(w3: Web3, block_count: int, newest_block_number: int) -> Tuple[
    List[int], List[float], List[int]]:
    base_fees = await w3.eth.fee_history(block_count, newest_block_number, [2, 98])
    base_fees_per_gas = base_fees["baseFeePerGas"]
    gas_used_ratio = base_fees["gasUsedRatio"]
    reward = base_fees["reward"]
    if len(base_fees_per_gas) == 0:
        raise RuntimeError("Unexpected error - no fees returned")

    return base_fees_per_gas, gas_used_ratio, reward


async def _fetch_coinbase_transfer(w3: Web3, block_number: int) -> int:
    # todo: get all miner payments
    #  https://github.com/flashbots/mev-inspect-py/blob/main/mev_inspect/miner_payments.py#L10
    pass


async def inspect_many_blocks(
        web3: Web3,
        after_block_number: int,
        before_block_number: int,
        host: str,
        inspect_db_session: orm.Session,
):
    """
    Inspects many blocks and writes them to DB.
    Fetches the miner revenue from block rewards and fees. (todo: MEV)
    Also fetched the transactions that are for time-locked contracts. (todo: ERC20 tokens)
    :param web3:
    :param after_block_number:
    :param before_block_number:
    :param host:
    :param inspect_db_session:
    :return:
    """
    logs_path = Path(config['logs']['logs_path']) / config['logs']['inspectors_log_path'] / f"inspector_{host}.log"
    log_file_handler = get_log_handler(logs_path, formatter, rotate=True)
    logger.addHandler(log_file_handler)

    all_blocks: List[Dict] = []
    all_updated_info: List[Dict] = []

    # get the addresses of all contracts and convert them to map of address to value
    smart_contracts = inspect_db_session.execute(
        select(ContractInfo.contract_address, ContractInfo.largest_tx_value)).all()
    smart_contracts = {contract_address: largest_tx_value for contract_address, largest_tx_value in smart_contracts}

    logger.info(f"Inspecting blocks {after_block_number} to {before_block_number}")
    # todo: check gas used ratio and reward
    base_fees_per_gas, gas_used_ratio, reward = await _fetch_base_fees_per_gas(web3,
                                                                               before_block_number - after_block_number,
                                                                               before_block_number)

    i = 0
    for block_number in range(after_block_number, before_block_number):
        logger.debug(f"Block: {block_number} -- Getting block data")

        miner_address, total_gas_used, block_gas_limit, block_transactions = await _fetch_block_info(web3, block_number)
        coinbase_transfer = 0
        total_gas_fee = 0

        for tx in block_transactions:
            total_gas_fee += (float(tx['gasPrice']) - base_fees_per_gas[i]) * float(tx['gas'])
            to_address = tx['to']
            from_address = tx['from']
            transaction_value = float(tx['value'])
            contract_address = None

            # check if it's from or to an already known contract
            if smart_contracts.get(to_address) is not None:
                contract_address = to_address
            elif smart_contracts.get(from_address) is not None:
                contract_address = from_address

            if contract_address is not None:
                if smart_contracts[contract_address] < transaction_value:
                    all_updated_info.append({
                        "contract_address": contract_address,
                        "largest_tx_hash": tx['hash'].hex(),
                        "largest_tx_block_number": block_number,
                        "largest_tx_value": transaction_value,
                    })
                    smart_contracts[contract_address] = transaction_value

            # coinbase transfer
            if to_address == miner_address:
                coinbase_transfer += transaction_value

        all_blocks.append({
            "block_number": block_number,
            "miner_address": miner_address,
            "coinbase_transfer": coinbase_transfer,
            "base_fee_per_gas": base_fees_per_gas[i],
            "gas_fee": total_gas_fee,
            "gas_used": total_gas_used,
            "gas_limit": block_gas_limit,
            "gas_used_ratio": gas_used_ratio[i],
        })

        i += 1

    if all_blocks:
        logger.debug("Writing to DB")
        insert_data(Block, all_blocks, inspect_db_session)
        logger.debug("Writing done")

    if all_updated_info:
        logger.debug("Updating DB")
        update_data(ContractInfo, all_updated_info, inspect_db_session)
        logger.debug("Updating done")

    clean_up_log_handlers(logger)

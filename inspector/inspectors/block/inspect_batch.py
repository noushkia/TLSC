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


async def inspect_many_blocks(
        web3: Web3,
        after_block_number: int,
        before_block_number: int,
        host: str,
        inspect_db_session: orm.Session,
) -> None:
    """
    Inspects many blocks and writes them to DB.
    Fetches the miner revenue from block rewards and fees. (todo: MEV)
    Also fetched the transactions that are for time-locked contracts. (todo: ERC20 tokens)
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

    all_blocks: List[Dict] = []
    all_updated_info: List[Dict] = []

    # get the addresses of all contracts and convert them to map of address to value
    # TODO: must update DB with new largest tx values.
    #  This is not local!
    smart_contracts = inspect_db_session.execute(
        select(ContractInfo.contract_address, ContractInfo.largest_tx_value)).all()
    smart_contracts = {contract_address: largest_tx_value for contract_address, largest_tx_value in smart_contracts}

    logger.info(f"Inspecting blocks {after_block_number} to {before_block_number}")

    base_fees_per_gas = await _fetch_base_fees_per_gas(web3,
                                                       before_block_number - after_block_number,
                                                       before_block_number - 1)

    i = 0
    for block_number in range(after_block_number, before_block_number):
        logger.debug(f"Block: {block_number} -- Getting block data")
        miner_address, total_gas_used, block_gas_limit, block_transactions = await _fetch_block_info(web3, block_number)
        coinbase_transfer = 0
        transaction_fees = 0
        burnt_fees = 0
        block_gas_used = 0

        for tx in block_transactions:
            # todo: use Etherscan API to faster fetch required data
            #  https://docs.etherscan.io/api-endpoints/blocks#get-block-and-uncle-rewards-by-blockno
            print(tx['hash'])
            tx_receipt = await web3.eth.get_transaction_receipt(tx['hash'])
            tx_gas_used = float(tx_receipt['gasUsed'])
            transaction_fees += (float(tx_receipt['effectiveGasPrice']) / ETH_TO_WEI) * tx_gas_used
            burnt_fees += (base_fees_per_gas[i] / ETH_TO_WEI) * tx_gas_used
            block_gas_used += tx_gas_used
            to_address = tx_receipt['to']
            from_address = tx_receipt['from']
            transaction_value = float(tx['value']) / ETH_TO_WEI

            # check if it's from or to an already known contract
            contract_address = None
            if smart_contracts.get(to_address) is not None:
                contract_address = to_address
            elif smart_contracts.get(from_address) is not None:
                contract_address = from_address

            if contract_address is not None and smart_contracts[contract_address] < transaction_value:
                all_updated_info.append({
                    "contract_address": contract_address,
                    "largest_tx_hash": tx['hash'].hex(),
                    "largest_tx_block_number": block_number,
                    "largest_tx_value": transaction_value,
                })
                smart_contracts[contract_address] = transaction_value

            if tx_receipt['to'] == miner_address:
                coinbase_transfer += transaction_value

        all_blocks.append({
            "block_number": block_number,
            "miner_address": miner_address,
            "coinbase_transfer": coinbase_transfer,
            "base_fee_per_gas": base_fees_per_gas[i],
            "gas_fee": transaction_fees - burnt_fees,  # priority_fee = gas_fee - base_fee (EIP-1559)
            "gas_used": total_gas_used,
            "gas_limit": block_gas_limit,
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

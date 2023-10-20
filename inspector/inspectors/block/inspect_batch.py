import configparser
import logging

from sqlalchemy import orm
from web3 import Web3

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


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
    pass

import logging
from typing import Tuple, List, Dict

import requests
from sqlalchemy import orm, select

from inspector.models.crud import insert_data
from inspector.models.verified_contract.model import VerifiedContract
from inspector.models.contract_info.model import ContractInfo
from inspector.models.contract.model import Contract


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def fetch_verified_contracts(contract_addresses: List[str],
                             etherscan_api_key: str,
                             logger: logging.Logger
                             ) -> List[Dict]:
    """
    Fetches verified contracts from Etherscan API and stores them in the database
    :param contract_addresses:   list of contract addresses
    :param etherscan_api_key:   Etherscan API key
    :param logger:   logger
    :return: list of verified contracts
    """
    # https://docs.etherscan.io/api-endpoints/contracts#get-contract-source-code-for-verified-contract-source-codes
    etherscan_contract_url = (
        f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={{}}&apikey={etherscan_api_key}")

    all_verified_contracts = []
    batch_size = 20
    i = 0
    for contract_address in contract_addresses:
        etherscan_response = requests.get(etherscan_contract_url.format(contract_address)).json()
        verified = etherscan_response['result'][0]['SourceCode'] is not None
        all_verified_contracts.append(
            {
                "contract_address": contract_address,
                "verified": verified,
                "contract_name": etherscan_response['result'][0]['ContractName'],
                "compiler_version": etherscan_response['result'][0]['CompilerVersion'],
                'evm_version': etherscan_response['result'][0]['EVMVersion'],
                'proxy': etherscan_response['result'][0]['Proxy'],
                'source_code': etherscan_response['result'][0]['SourceCode']
            }
        )
        i += 1
        if i % batch_size == 0:
            logger.info(f"Verified {i} contracts")

    return all_verified_contracts


def inspect_verified_contracts(inspect_db_session: orm.Session,
                               task_batch: Tuple[int, int],
                               etherscan_api_key: str
                               ):
    """
    Fetches verified contracts from Etherscan API and stores them in the database
    :param inspect_db_session:  database session
    :param task_batch:  tuple of (start_block, end_block)
    :param etherscan_api_key:  Etherscan API key
    :return:  None
    """
    logger = setup_logger()
    logger.info(f"Starting up verified contract inspector for blocks {task_batch[0]} to {task_batch[1]}")

    # get contract addresses from the database that were created in the given block range,
    # are in ContractsInfo db i.e., have non-zero balance, and are not in VerifiedContracts db
    vc_query_response = inspect_db_session.execute(
        select(Contract.contract_address).
        join(ContractInfo, Contract.contract_address == ContractInfo.contract_address).
        where((task_batch[0] <= Contract.block_number) & (Contract.block_number <= task_batch[1])).
        where(~Contract.contract_address.in_(
            inspect_db_session.query(VerifiedContract.contract_address).all()
        ))
    ).all()
    contract_addresses = [contract_address for contract_address, in vc_query_response]
    all_verified_contracts = fetch_verified_contracts(contract_addresses, etherscan_api_key, logger)

    if all_verified_contracts:
        logger.debug("Writing to DB")
        insert_data(VerifiedContract, all_verified_contracts, inspect_db_session)
        logger.debug("Writing done")

    logger.info(f"Finished verified contract inspector for blocks {task_batch[0]} to {task_batch[1]}")

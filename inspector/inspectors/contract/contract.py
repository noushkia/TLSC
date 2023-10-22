import asyncio
import configparser
import logging
import traceback
from asyncio import CancelledError
from typing import List, Tuple

from sqlalchemy import orm, select, and_

from inspector.base import Inspector
from inspector.inspectors.contract.inspect_batch import inspect_many_contracts
from inspector.models.contract.model import Contract

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')


class ContractInspector(Inspector):
    async def inspect_many(self, inspect_db_session: orm.Session, task_batch: Tuple[int, int] | List[Tuple[int, str]],
                           batch_size: int = 50):
        contract_addresses = inspect_db_session.execute(
            select(Contract.block_number, Contract.contract_address).
            where(and_(task_batch[0] <= Contract.block_number, Contract.block_number <= task_batch[1]))
        ).all()

        tasks = []
        sem = asyncio.Semaphore(self.max_concurrency)
        # inspect each batch of contracts
        for i in range(0, len(contract_addresses), batch_size):
            tasks.append(
                asyncio.ensure_future(
                    self.safe_inspect_many(
                        inspect_db_session=inspect_db_session,
                        task_batch=contract_addresses[i:min(i + batch_size, len(contract_addresses))],
                        semaphore=sem
                    )
                )
            )

        logger.info(f"{self.host}: Gathered {len(contract_addresses)} contracts to inspect")
        try:
            await asyncio.gather(*tasks)
        except CancelledError:
            logger.info(f"{self.host}: Requested to exit, cleaning up...")
        except Exception:
            logger.error(f"{self.host}: Exited due to {traceback.print_exc()}")
            raise

    async def safe_inspect_many(self, inspect_db_session: orm.Session, semaphore: asyncio.Semaphore,
                                task_batch: Tuple[int, int] | List[str]):
        async with semaphore:
            await self.batch_queue.put(await inspect_many_contracts(
                self.w3,
                contracts=task_batch,
                host=self.host,
                inspect_db_session=inspect_db_session,
            ))

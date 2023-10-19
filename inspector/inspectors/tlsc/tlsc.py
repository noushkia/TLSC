import asyncio
import configparser
import logging
import traceback
from asyncio import CancelledError
from typing import Tuple

from sqlalchemy import orm, desc
from sqlalchemy.orm import Session

from inspector.base import Inspector
from inspector.models.contract.model import Contract
from inspector.inspectors.tlsc.inspect_batch import inspect_many_blocks

config = configparser.ConfigParser()
config.read('config.ini')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')


def _get_last_inspected_block(session: Session, after_block: int, before_block: int) -> int:
    """
    Gets the last block that was inspected and stored on DB.
    Might be better to modify it and move it to pre-exec stages.
    :param session: DB session
    :param after_block: The block to start inspecting from
    :param before_block: The block to stop inspecting at
    :return: The last block that was inspected
    """
    latest_block = session.query(Contract.block_number) \
        .filter(Contract.block_number < before_block) \
        .order_by(desc(Contract.block_number)) \
        .first()
    if latest_block is not None and latest_block[0] > after_block:
        after_block = latest_block[0] + 1

    return after_block


class TLSCInspector(Inspector):

    async def inspect_many(
            self,
            inspect_db_session: orm.Session,
            task_batch: Tuple[int, int],
            batch_size: int = 20,
    ):
        after_block, before_block = task_batch
        after_block = _get_last_inspected_block(inspect_db_session, after_block, before_block)

        tasks = []
        sem = asyncio.Semaphore(self.max_concurrency)
        for block_number in range(after_block, before_block, batch_size):
            batch_after_block = block_number
            batch_before_block = min(block_number + batch_size, before_block)
            tasks.append(
                asyncio.ensure_future(
                    self.safe_inspect_many(
                        inspect_db_session=inspect_db_session,
                        task_batch=(batch_after_block, batch_before_block),
                        semaphore=sem
                    )
                )
            )

        logger.info(f"{self.host}: Gathered {before_block - after_block} blocks to inspect")
        try:
            await asyncio.gather(*tasks)
        except CancelledError:
            logger.info(f"{self.host}: Requested to exit, cleaning up...")
        except Exception:
            logger.error(f"{self.host}: Exited due to {traceback.print_exc()}")
            raise

    async def safe_inspect_many(
            self,
            inspect_db_session: orm.Session,
            semaphore: asyncio.Semaphore,
            task_batch: Tuple[int, int],
    ):
        after_block_number, before_block_number = task_batch
        async with semaphore:
            await self.batch_queue.put(await inspect_many_blocks(
                self.w3,
                after_block_number,
                before_block_number,
                host=self.host,
                inspect_db_session=inspect_db_session,
            ))

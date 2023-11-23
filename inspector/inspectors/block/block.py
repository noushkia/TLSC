import asyncio
import traceback
from asyncio import CancelledError
from typing import Tuple, List

from sqlalchemy import orm, desc
from sqlalchemy.orm import Session

from inspector.base import Inspector
from inspector.inspectors.block.inspect_batch import inspect_many_blocks, inspect_many_attributes
from inspector.models.block.model import Block
from inspector.utils import configure_logger, clean_up_log_handlers


def _get_last_inspected_block(session: Session, after_block: int, before_block: int, attributes: List[str]) -> int:
    """
    Gets the last block that was inspected and stored on DB.
    Might be better to modify it and move it to pre-exec stages.
    :param session: DB session
    :param after_block: The block to start inspecting from
    :param before_block: The block to stop inspecting at
    :param attributes: Attributes to inspect None if full block is inspected
    :return: The last block that was inspected
    todo: update for SQLAlchemy 2.0
    """
    if attributes is None:
        latest_block = session.query(Block.block_number) \
            .filter(Block.block_number < before_block) \
            .order_by(desc(Block.block_number)) \
            .first()
        if latest_block is not None and latest_block[0] > after_block:
            after_block = latest_block[0] + 1
    else:
        # todo: For now it's just tx_count, need to update for other attributes
        latest_block = session.query(Block.block_number) \
            .filter(Block.block_number < before_block) \
            .filter(Block.tx_count.isnot(None)) \
            .order_by(desc(Block.block_number)) \
            .first()
        if latest_block is not None and latest_block[0] > after_block:
            after_block = latest_block[0] + 1

    return after_block


class BlockInspector(Inspector):
    def __init__(
            self,
            rpc_endpoint: str,
            max_concurrency: int = 1,
            request_timeout: int = 300,
            etherscan_api_key: str = "",
            attributes: list = None,
    ):
        super().__init__(rpc_endpoint, max_concurrency, request_timeout)
        self.etherscan_api_key = etherscan_api_key
        self.attributes = attributes

    async def inspect_many(
            self,
            inspect_db_session: orm.Session,
            task_batch: Tuple[int, int],
            batch_size: int = 20,
    ):
        self.logger = configure_logger(self.host)
        after_block, before_block = task_batch

        after_block = _get_last_inspected_block(inspect_db_session, after_block, before_block, self.attributes)

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

        self.logger.info(f"{self.host}: Gathered {before_block - after_block} blocks to inspect")
        try:
            await asyncio.gather(*tasks)
        except CancelledError:
            self.logger.info(f"{self.host}: Requested to exit, cleaning up...")
        except Exception:
            self.logger.error(f"{self.host}: Exited due to {traceback.print_exc()}")
            raise
        finally:
            clean_up_log_handlers(self.logger)

    async def safe_inspect_many(
            self,
            inspect_db_session: orm.Session,
            semaphore: asyncio.Semaphore,
            task_batch: Tuple[int, int],
    ):
        after_block_number, before_block_number = task_batch
        async with semaphore:
            if self.attributes is None:
                # https://docs.etherscan.io/api-endpoints/blocks#get-block-and-uncle-rewards-by-blockno
                etherscan_block_reward_url = (
                    f"https://api.etherscan.io/api?module=block&action=getblockreward&blockno={{"
                    f"}}&apikey={self.etherscan_api_key}")
                await self.batch_queue.put(await inspect_many_blocks(
                    self.w3,
                    after_block_number,
                    before_block_number,
                    logger=self.logger,
                    inspect_db_session=inspect_db_session,
                    etherscan_block_reward_url=etherscan_block_reward_url,
                ))
            else:
                await self.batch_queue.put(await inspect_many_attributes(
                    self.w3,
                    after_block_number,
                    before_block_number,
                    logger=self.logger,
                    inspect_db_session=inspect_db_session,
                    attributes=self.attributes,
                ))

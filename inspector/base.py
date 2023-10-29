import asyncio
from abc import abstractmethod, ABC
from asyncio import Queue
from typing import Tuple, List

from sqlalchemy import orm

from web3 import Web3
from web3.eth import AsyncEth

from inspector.provider import get_base_provider


class Inspector(ABC):
    def __init__(
            self,
            rpc_endpoint: str,
            max_concurrency: int = 1,
            request_timeout: int = 300,
    ):
        base_provider = get_base_provider(rpc_endpoint, request_timeout=request_timeout)
        self.w3 = Web3(base_provider, modules={"eth": (AsyncEth,)}, middlewares=[])
        self.host = rpc_endpoint.split(":")[1].strip("/")
        self.max_concurrency = max_concurrency
        self.batch_queue = Queue()
        self.logger = None

    @abstractmethod
    async def inspect_many(
            self,
            inspect_db_session: orm.Session,
            task_batch: Tuple[int, int] | List[str],
            batch_size: int = 20,
    ):
        pass

    @abstractmethod
    async def safe_inspect_many(
            self,
            inspect_db_session: orm.Session,
            semaphore: asyncio.Semaphore,
            task_batch: Tuple[int, int] | List[str],
    ):
        pass

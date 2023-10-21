from typing import List, Dict, Type

from sqlalchemy import orm, insert, update

from inspector.models.block.model import Block
from inspector.models.contract.model import Contract
from inspector.models.contract_info.model import ContractInfo


def insert_data(
        table: Type[Contract] | Type[ContractInfo] | Type[Block],
        values: List[Dict],
        db_session: orm.Session,
) -> None:
    db_session.execute(insert(table=table), values)
    db_session.commit()


def update_data(
        table: Type[Contract] | Type[ContractInfo] | Type[Block],
        values: List[Dict],
        db_session: orm.Session,
) -> None:
    db_session.execute(update(table=table), values)
    db_session.commit()

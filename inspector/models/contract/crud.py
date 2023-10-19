from typing import List

from sqlalchemy import orm

from inspector.models.contract.model import Contract


def write_contracts(
        contracts: List[Contract],
        db_session: orm.Session,
) -> None:
    db_session.bulk_save_objects(contracts)
    db_session.commit()

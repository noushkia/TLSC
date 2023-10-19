from typing import List

from sqlalchemy import orm

from inspector.models.contract_info.model import ContractInfo


def write_contracts_info(
        contracts_info: List[ContractInfo],
        db_session: orm.Session,
) -> None:
    db_session.bulk_save_objects(contracts_info)
    db_session.commit()

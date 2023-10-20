from typing import List

from sqlalchemy import orm

from inspector.models.block.model import Block


def write_blocks(
        blocks: List[Block],
        db_session: orm.Session,
) -> None:
    db_session.bulk_save_objects(blocks)
    db_session.commit()

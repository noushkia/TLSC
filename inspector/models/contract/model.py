from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from inspector.models.base import Base


class Contract(Base):
    __tablename__ = 'contracts'

    contract_address: Mapped[str] = mapped_column(String(100), primary_key=True, default="0x0")
    bytecode: Mapped[str] = mapped_column(Text, nullable=True)  # TODO: Can remove it later
    from_address: Mapped[str] = mapped_column(String(100), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self):
        return f"<Contract(contract_address='{self.contract_address}', " \
               f"bytecode='{self.bytecode}', " \
               f"from_address='{self.from_address}', " \
               f"tx_hash='{self.tx_hash}', " \
               f"block_number='{self.block_number}')>"

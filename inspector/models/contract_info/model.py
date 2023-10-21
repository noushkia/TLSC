from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from inspector.models.base import Base


class ContractInfo(Base):
    __tablename__ = 'contracts_info'

    contract_address: Mapped[str] = mapped_column(String(100), primary_key=True, default="0x0")
    eth_balance: Mapped[float] = mapped_column(Float, nullable=False)
    largest_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    largest_tx_block_number: Mapped[int] = mapped_column(Integer, nullable=True)
    largest_tx_value: Mapped[float] = mapped_column(Float, nullable=True)

    def __repr__(self):
        return f"<ContractInfo(contract_address='{self.contract_address}', " \
               f"eth_balance='{self.eth_balance}', " \
               f"largest_tx_hash='{self.largest_tx_hash}', " \
               f"largest_tx_block_number='{self.largest_tx_block_number}', " \
               f"largest_tx_value='{self.largest_tx_value}')>"

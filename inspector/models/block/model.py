from sqlalchemy import Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from inspector.models.base import Base


class Block(Base):
    __tablename__ = 'blocks'

    block_number: Mapped[int] = mapped_column(Integer, primary_key=True, default=0)
    miner_address: Mapped[str] = mapped_column(String(100), nullable=False)
    coinbase_transfer: Mapped[float] = mapped_column(Numeric, nullable=False)
    base_fee_per_gas: Mapped[float] = mapped_column(Numeric, nullable=False)
    gas_fee: Mapped[float] = mapped_column(Numeric, nullable=False)
    gas_used: Mapped[float] = mapped_column(Numeric, nullable=False)
    gas_limit: Mapped[float] = mapped_column(Numeric, nullable=False)
    tx_count: Mapped[float] = mapped_column(Numeric, nullable=True)

    def __repr__(self):
        return f"<Block(block_number='{self.block_number}', " \
               f"miner_address='{self.miner_address}', " \
               f"coinbase_transfer='{self.coinbase_transfer}', " \
               f"base_fee_per_gas='{self.base_fee_per_gas}', " \
               f"gas_fee='{self.gas_fee}', " \
               f"gas_used='{self.gas_used}', " \
               f"gas_limit='{self.gas_limit}', >" \
               f"tx_count='{self.tx_count}', >"

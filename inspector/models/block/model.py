from sqlalchemy import Column, Integer, String, Numeric

from inspector.models.base import Base


class Block(Base):
    __tablename__ = 'blocks'

    block_number = Column(Integer, primary_key=True)  # the block number
    miner_address = Column(String, nullable=False)  # the block miner/validator address
    coinbase_transfer = Column(Numeric, nullable=False)  # the coinbase transfer, i.e., block reward
    base_fee_per_gas = Column(Numeric, nullable=False)  # the base fee per gas for the block
    gas_fee = Column(Numeric, nullable=False)  # Total gas fee in the block
    gas_used = Column(Numeric, nullable=False)  # Total gas used in the block
    # todo: add MEV (all payments to the miner)

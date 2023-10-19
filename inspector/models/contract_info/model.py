from sqlalchemy import Column, Integer, String, Float

from inspector.models.base import Base


class ContractInfo(Base):
    __tablename__ = 'contracts_info'

    contract_address = Column(String(100), primary_key=True)
    eth_balance = Column(Float)
    largest_tx_hash = Column(String(100))
    largest_tx_block_number = Column(Integer)
    largest_tx_value = Column(Float)

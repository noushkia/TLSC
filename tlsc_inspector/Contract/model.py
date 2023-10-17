from sqlalchemy import Column, Integer, Text, String

from tlsc_inspector.Contract.base import Base


class Contract(Base):
    __tablename__ = 'contracts'

    contract_address = Column(String(100), primary_key=True)
    bytecode = Column(Text)
    from_address = Column(String(50))
    tx_hash = Column(String(100))
    block_number = Column(Integer)

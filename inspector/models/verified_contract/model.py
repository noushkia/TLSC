from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from inspector.models.base import Base


class VerifiedContract(Base):
    __tablename__ = 'verified-contracts'

    contract_address: Mapped[str] = mapped_column(String(100), primary_key=True, default="0x0")
    verified: Mapped[bool] = mapped_column(String(100), nullable=False, default=False)
    contract_name: Mapped[str] = mapped_column(String(100), nullable=True)
    compiler_version: Mapped[str] = mapped_column(String(100), nullable=True)
    evm_version: Mapped[str] = mapped_column(String(100), nullable=True)
    proxy: Mapped[str] = mapped_column(String(100), nullable=True)
    sourcecode: Mapped[str] = mapped_column(Text, nullable=True)  # if None -> Not verified

    def __repr__(self):
        return f"<Contract(contract_address='{self.contract_address}', " \
               f"verified='{self.verified}', " \
               f"contract_name='{self.contract_name}', " \
               f"compiler_version='{self.compiler_version}', " \
               f"evm_version='{self.evm_version}', " \
               f"proxy='{self.proxy}', " \
               f"sourcecode='{self.sourcecode}')>"

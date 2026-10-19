from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, String
from src.database import Base

class SchemaManifest(BaseModel):
    """
    Data contract that drives validation and matching.
    """
    version: str = "1.0"
    lambda_details = lambda: ["txn_ref", "value_date", "currency", "amount"]
    
    join_keys: List[str] = Field(
        default_factory=lambda_details
    )
    
    amount_tolerance: Decimal = Field(default=Decimal("0.01"))
    
    required_fields_ledger: List[str] = Field(
        default_factory= lambda_details
    )
    
    required_fields_settlement: List[str] = Field(
        default_factory= lambda_details
    )
    
    date_format: str = "%Y-%m-%d"

class SchemaRecord(Base):
    __tablename__ = "schema_manifests"
    
    # We use String as the primary key here since there's only ever one active schema, 
    # or you can use a standard Integer primary key.
    version: Mapped[str] = mapped_column(String, primary_key=True)
    join_keys: Mapped[list] = mapped_column(JSON)
    amount_tolerance: Mapped[str] = mapped_column(String) # Store Decimal as string in SQLite
    required_fields_ledger: Mapped[list] = mapped_column(JSON)
    required_fields_settlement: Mapped[list] = mapped_column(JSON)
    date_format: Mapped[str] = mapped_column(String)
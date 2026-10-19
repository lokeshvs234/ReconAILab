from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete
from src.database import get_db
from src.models.schema import SchemaManifest, SchemaRecord

router = APIRouter(tags=["Schema"])

@router.get("/schema/manifest", response_model=SchemaManifest)
def get_schema_manifest(db: Session = Depends(get_db)):
    record = db.query(SchemaRecord).first()
    if not record:
        raise HTTPException(status_code=404, detail="Schema manifest not found")
    
    # Manually convert string amount_tolerance back to Decimal for the Pydantic model
    return SchemaManifest(
        version=record.version,
        join_keys=record.join_keys,
        amount_tolerance=record.amount_tolerance,
        required_fields_ledger=record.required_fields_ledger,
        required_fields_settlement=record.required_fields_settlement,
        date_format=record.date_format
    )

@router.post("/schema/manifest", response_model=SchemaManifest)
def update_schema_manifest(manifest: SchemaManifest, db: Session = Depends(get_db)):
    # Delete existing schema to ensure we only have one active contract
    db.execute(delete(SchemaRecord))
    
    # The BankLite Process: Dump the Pydantic model and unpack into SQLAlchemy
    data = manifest.model_dump()
    
    # Convert Decimal to string because SQLite cannot store Decimals natively
    data["amount_tolerance"] = str(data["amount_tolerance"])
    
    # Create the database object
    new_record = SchemaRecord(**data)
    
    # Save to database
    db.add(new_record)
    db.commit()
    
    return manifest
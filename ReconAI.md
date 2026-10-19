**ReconAI – Simple REST API Case Study & Complete Implementation Guide**

*(Pure FastAPI + deterministic processing – no agents, no LLM)*

---

## 1. Case Study Details

**Title**  
ReconAI – Simple REST API for Banking Reconciliation

**Business Context**  
A bank needs a reliable system to compare its internal ledger with external settlement files received from card networks / payment processors.

The system must:
- Accept ledger and settlement files
- Validate every record against a defined schema
- Detect missing records, amount mismatches and duplicates
- Calculate control totals (row counts and amount sums)
- Create exception records for mismatches
- Allow human reviewers to record dispositions (approve / reject / rework)
- Maintain a full audit trail of every action

**Key Design Principle**  
All matching and decision logic is **100% deterministic**.  
No artificial intelligence, no language models, and no autonomous agents are used in this version.  
This clean REST foundation can later be extended with agentic capabilities.

**Primary Data Files (synthetic)**  
- `data/ledger.csv`  
- `data/settlement.csv`  
- `data/duplicate_settlement.csv`  
- `data/bad_amount.csv`

**Success Criteria**  
- Schema validation catches bad data  
- Control totals reconcile to the raw files  
- Deterministic matcher correctly identifies all mismatches  
- Every disposition is audited with actor identity  
- The entire system is exposed through a clean REST API

---

## 2. Complete List of Endpoints

| #  | Method | Endpoint                                 | Purpose                                          |
|----|--------|------------------------------------------|--------------------------------------------------|
| 1  | GET    | `/health`                                | Liveness / readiness check                       |
| 2  | GET    | `/schema/manifest`                       | Retrieve current schema contract                 |
| 3  | POST   | `/schema/manifest`                       | Update / replace schema contract                 |
| 4  | POST   | `/ingest/ledger`                         | Upload & validate ledger CSV                     |
| 5  | POST   | `/ingest/settlement`                     | Upload & validate settlement CSV                 |
| 6  | GET    | `/control-totals`                        | Retrieve control-total report                    |
| 7  | POST   | `/control-totals`                        | Recompute control totals for a batch             |
| 8  | POST   | `/match`                                 | Run deterministic matcher                        |
| 9  | GET    | `/exceptions`                            | List exceptions (filterable + paginated)         |
| 10 | GET    | `/exceptions/{exception_id}`             | Get full details of one exception                |
| 11 | POST   | `/exceptions/{exception_id}/disposition` | Record human disposition (approve/reject/rework) |
| 12 | GET    | `/audit/{exception_id}`                  | Retrieve full audit trail of an exception        |

---

## 3. Why Exception Details Use the GET Method

In REST design:

- **GET** is used for **retrieving** a resource (safe, idempotent, cacheable).
- **POST** is used for **creating** a resource or triggering an action that changes state.

Fetching the details of a single exception is a pure **read** operation.  
It does not create, update, or delete anything. Therefore the correct HTTP method is **GET**.

Benefits:
- The URL can be bookmarked or shared
- Clients can cache the response
- It follows the standard REST pattern:  
  `GET /collection` → list  
  `GET /collection/{id}` → single item details

The only endpoint that **changes** the exception status is the disposition endpoint, which correctly uses **POST**.

---

## 4. Project Structure

```
reconai/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── schema.py
│   │   ├── exception.py
│   │   └── common.py
│   ├── services/
│   │   ├── validator.py
│   │   ├── control_totals.py
│   │   ├── matcher.py
│   │   ├── exception_service.py
│   │   └── audit.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── schema.py
│   │   ├── ingest.py
│   │   ├── match.py
│   │   ├── exceptions.py
│   │   └── audit.py
│   └── utils/
│       ├── file_handlers.py
│       └── ids.py
├── data/
├── storage/
├── tests/
├── .env
├── requirements.txt
└── README.md
```

---

## 5. Configuration & Database Setup

### 5.1 `src/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "ReconAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./storage/reconai.db"
    STORAGE_DIR: str = "storage"
    UPLOAD_DIR: str = "storage/uploads"
    DEFAULT_AMOUNT_TOLERANCE: str = "0.01"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 5.2 `src/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5.3 `.env`

```env
APP_NAME=ReconAI
APP_VERSION=1.0.0
DEBUG=True
DATABASE_URL=sqlite:///./storage/reconai.db
STORAGE_DIR=storage
UPLOAD_DIR=storage/uploads
DEFAULT_AMOUNT_TOLERANCE=0.01
```

---

## 6. Detailed Endpoint Specifications

### 6.1 Health Check

**Endpoint:** `GET /health`  
**Purpose:** Liveness and readiness probe.

**Input:** None

**Detailed Process (Complete Implementation Guide)**

1. Create the file `src/routers/health.py`.
2. Add the following imports at the top of the file:
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from sqlalchemy import text
   from datetime import datetime, timezone
   from src.config import get_settings
   from src.database import get_db
   ```
3. Create the router object:
   ```python
   router = APIRouter(tags=["Health"])
   ```
4. Create the endpoint function:
   ```python
   @router.get("/health")
   def health_check(db: Session = Depends(get_db)):
   ```
5. Inside the function, read settings:
   ```python
       settings = get_settings()
   ```
6. Optionally check database connectivity:
   ```python
       try:
           db.execute(text("SELECT 1"))
           db_status = "connected"
       except Exception:
           db_status = "unavailable"
   ```
7. Build the response dictionary:
   ```python
       return {
           "status": "ok",
           "app_name": settings.APP_NAME,
           "version": settings.APP_VERSION,
           "database": db_status,
           "timestamp": datetime.now(timezone.utc).isoformat()
       }
   ```
8. Register the router in `src/main.py`:
   ```python
   from src.routers import health
   app.include_router(health.router)
   ```

**Output Example:**
```json
{
  "status": "ok",
  "app_name": "ReconAI",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-10-15T08:35:00+00:00"
}
```

**Workflow:**  
Client → GET /health → Read settings → Optional DB check → Return JSON

**Concepts Used:** Configuration reading, dependency injection, health-check pattern

---

### 6.2 Get Schema Manifest

**Endpoint:** `GET /schema/manifest`  
**Purpose:** Return the current data contract used for validation and matching.

**Input:** None

**Detailed Process (Complete Implementation Guide)**

1. Create / update `src/models/schema.py` and define the model:
   ```python
   from pydantic import BaseModel
   from decimal import Decimal
   from typing import List

   class SchemaManifest(BaseModel):
       version: str
       join_keys: List[str]
       amount_tolerance: Decimal
       required_fields_ledger: List[str]
       required_fields_settlement: List[str]
       date_format: str
   ```
2. Create the file `src/routers/schema.py` (if it does not exist).
3. Add imports:
   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy.orm import Session
   from src.database import get_db
   from src.models.schema import SchemaManifest
   ```
4. Create the router:
   ```python
   router = APIRouter(tags=["Schema"])
   ```
5. Create the endpoint:
   ```python
   @router.get("/schema/manifest", response_model=SchemaManifest)
   def get_schema_manifest(db: Session = Depends(get_db)):
   ```
6. Inside the function, query the database for the latest schema record (or load from a JSON file).
7. If no record is found, raise an exception:
   ```python
       raise HTTPException(status_code=404, detail="Schema manifest not found")
   ```
8. Convert the database row into a `SchemaManifest` instance and return it.
9. Register the router in `main.py`.

**Output Example:**
```json
{
  "version": "1.0",
  "join_keys": ["txn_ref", "value_date", "currency"],
  "amount_tolerance": "0.01",
  "required_fields_ledger": ["txn_ref", "value_date", "currency", "amount"],
  "required_fields_settlement": ["txn_ref", "value_date", "currency", "amount"],
  "date_format": "%Y-%m-%d"
}
```

**Workflow:**  
Client → GET /schema/manifest → Load from DB → Validate with Pydantic → 200 OK

**Concepts Used:** Pydantic response model, database session, HTTP 404

---

### 6.3 Update Schema Manifest

**Endpoint:** `POST /schema/manifest`  
**Purpose:** Replace the current schema contract.

**Input:** JSON body that matches the `SchemaManifest` model.

**Detailed Process (Complete Implementation Guide)**

1. In `src/routers/schema.py` add the following endpoint:
   ```python
   @router.post("/schema/manifest", response_model=SchemaManifest)
   def update_schema_manifest(
       manifest: SchemaManifest,
       db: Session = Depends(get_db)
   ):
   ```
2. FastAPI automatically validates the incoming JSON against the `SchemaManifest` model.  
   If validation fails, FastAPI returns HTTP 422 with detailed errors – no extra code is required.
3. Delete any existing schema record (or update it).
4. Create a new database object from the validated manifest:
   ```python
       data = manifest.model_dump()
       # create SQLAlchemy model instance from data
   ```
5. Add the new record to the session and commit:
   ```python
       db.add(new_record)
       db.commit()
       db.refresh(new_record)
   ```
6. Return the saved `SchemaManifest` object.

**Output:** Same structure as the GET response.

**Workflow:**  
Client → POST /schema/manifest → Auto-validation → Persist → 200 OK

**Concepts Used:** Request body validation, database session, atomic update

---

### 6.4 Ingest Ledger File

**Endpoint:** `POST /ingest/ledger`  
**Purpose:** Upload a ledger CSV, validate every row, detect duplicates and calculate control totals.

**Input:**  
- Content-Type: `multipart/form-data`  
- Form field name: `file`  
- Optional query parameter: `batch_id`

**Detailed Process (Complete Implementation Guide)**

1. Create the file `src/routers/ingest.py`.
2. Add the required imports:
   ```python
   from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
   from sqlalchemy.orm import Session
   from decimal import Decimal, InvalidOperation
   from datetime import datetime
   import csv, uuid, os
   from io import StringIO
   from src.config import get_settings
   from src.database import get_db
   ```
3. Create the router:
   ```python
   router = APIRouter(tags=["Ingest"])
   ```
4. Create the endpoint function:
   ```python
   @router.post("/ingest/ledger")
   async def ingest_ledger(
       file: UploadFile = File(...),
       batch_id: str | None = Query(None),
       db: Session = Depends(get_db)
   ):
   ```
5. Read configuration:
   ```python
       settings = get_settings()
       upload_dir = settings.UPLOAD_DIR
   ```
6. Generate a batch_id if the client did not supply one:
   ```python
       if not batch_id:
           batch_id = str(uuid.uuid4())
   ```
7. Save the uploaded file to disk:
   ```python
       os.makedirs(upload_dir, exist_ok=True)
       file_path = os.path.join(upload_dir, f"{batch_id}_ledger.csv")
       content = await file.read()
       with open(file_path, "wb") as f:
           f.write(content)
   ```
8. Parse the CSV content:
   ```python
       text = content.decode("utf-8")
       reader = csv.DictReader(StringIO(text))
       rows = list(reader)
   ```
9. Load the current schema manifest (from database or file).
10. Initialise containers:
    ```python
        valid_rows = []
        exceptions = []
    ```
11. Validate every row (core loop):
    ```python
        for idx, row in enumerate(rows, start=1):
            # Check required fields
            # Try Decimal conversion for amount
            # Check currency length == 3
            # Parse date
            # On any failure append to exceptions list
            # On success append cleaned row to valid_rows
    ```
12. Build dictionary index and detect duplicates:
    ```python
        ledger_index = {}
        seen_keys = set()
        duplicates = []
        for row in valid_rows:
            key = (row["txn_ref"], row["currency"])
            if key in seen_keys:
                duplicates.append(row["txn_ref"])
            else:
                seen_keys.add(key)
                ledger_index[key] = row
    ```
13. Calculate control totals:
    - Count total rows, valid rows, invalid rows.
    - Sum amounts grouped by currency using `Decimal`.
14. Persist the results using the database session (`db.add(...)`, `db.commit()`).
15. Build and return the response dictionary:
    ```python
        return {
            "batch_id": batch_id,
            "source": "ledger",
            "row_count": len(rows),
            "valid_count": len(valid_rows),
            "invalid_count": len(exceptions),
            "control_totals": control_totals,
            "duplicates": duplicates,
            "exceptions": exceptions
        }
    ```

**Output Example:**
```json
{
  "batch_id": "BAT-20261015-001",
  "source": "ledger",
  "row_count": 1250,
  "valid_count": 1245,
  "invalid_count": 5,
  "control_totals": {"USD": "1250000.00"},
  "duplicates": ["TXN-99881"],
  "exceptions": [
    {"row": 42, "rule": "amount_not_numeric", "message": "Cannot convert 'N/A' to Decimal"}
  ]
}
```

**Workflow:**  
Client → POST /ingest/ledger → Save file → Parse CSV → Validate rows → Index + detect duplicates → Control totals → Persist → 200 OK

**Concepts Used:** File upload, CSV parsing, loops & conditionals, dictionary indexing, set-based duplicate detection, Decimal arithmetic, database session

---

### 6.5 Ingest Settlement File

**Endpoint:** `POST /ingest/settlement`

**Detailed Process (Complete Implementation Guide)**

1. Copy the entire `ingest_ledger` function.
2. Change the path decorator to `@router.post("/ingest/settlement")`.
3. Change the function name to `ingest_settlement`.
4. Inside the function:
   - Use `required_fields_settlement` from the schema instead of ledger fields.
   - Save the file as `{batch_id}_settlement.csv`.
   - Store results in settlement-related tables.
   - Set `"source": "settlement"` in the returned JSON.
5. All other logic (validation, indexing, control totals, persistence) remains exactly the same.

**Concepts Used:** Code reuse, shared validation and control-total services

---

### 6.6 Get Control Totals

**Endpoint:** `GET /control-totals`  
**Purpose:** Return the control-total report for a given batch.

**Input:** Query parameter `batch_id` (required)

**Detailed Process (Complete Implementation Guide)**

1. In `src/routers/ingest.py` (or a dedicated control-totals router) add:
   ```python
   @router.get("/control-totals")
   def get_control_totals(
       batch_id: str = Query(...),
       db: Session = Depends(get_db)
   ):
   ```
2. Query the control-totals table for the given `batch_id`.
3. If no record is found:
   ```python
       raise HTTPException(status_code=404, detail="Control totals not found for this batch")
   ```
4. Return the record as a dictionary / Pydantic model.

**Output Example:**
```json
{
  "batch_id": "BAT-20261015-001",
  "ledger": {"row_count": 1250, "totals": {"USD": "1250000.00"}},
  "settlement": {"row_count": 1248, "totals": {"USD": "1248500.00"}},
  "difference": {"USD": "1500.00"}
}
```

**Workflow:**  
Client → GET /control-totals?batch_id=xxx → Query DB → 200 OK or 404

**Concepts Used:** Query parameter binding, database session, HTTP 404

---

### 6.7 Recompute Control Totals

**Endpoint:** `POST /control-totals`  
**Purpose:** Force recalculation of control totals using already ingested data.

**Input:**
```json
{"batch_id": "BAT-20261015-001"}
```

**Detailed Process (Complete Implementation Guide)**

1. Define a small request model:
   ```python
   from pydantic import BaseModel
   class RecomputeRequest(BaseModel):
       batch_id: str
   ```
2. Create the endpoint:
   ```python
   @router.post("/control-totals")
   def recompute_control_totals(
       body: RecomputeRequest,
       db: Session = Depends(get_db)
   ):
   ```
3. Load the previously saved valid ledger rows and settlement rows for `body.batch_id`.
4. Call the same control-totals calculation logic used during ingest.
5. Update the existing control-totals record in the database.
6. Commit the transaction.
7. Return the newly calculated report.

**Workflow:**  
Client → POST /control-totals → Load existing data → Recompute → Update DB → 200 OK

**Concepts Used:** Idempotent recalculation, database session, service reuse

---

### 6.8 Run Deterministic Matcher

**Endpoint:** `POST /match`  
**Purpose:** Compare ledger and settlement data and create exception records.  
This is the single source of truth for match status.

**Input:**
```json
{"batch_id": "BAT-20261015-001"}
```

**Detailed Process (Complete Implementation Guide)**

1. Create `src/routers/match.py`.
2. Add imports:
   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from sqlalchemy.orm import Session
   from decimal import Decimal
   import uuid
   from src.config import get_settings
   from src.database import get_db
   ```
3. Define a request model:
   ```python
   class MatchRequest(BaseModel):
       batch_id: str
   ```
4. Create the endpoint:
   ```python
   @router.post("/match")
   def run_match(body: MatchRequest, db: Session = Depends(get_db)):
   ```
5. Read settings and tolerance:
   ```python
       settings = get_settings()
       tolerance = Decimal(settings.DEFAULT_AMOUNT_TOLERANCE)
   ```
6. Load the ledger index and settlement index for the given batch_id from the database.  
   If either is missing, raise HTTP 404.
7. Prepare containers:
   ```python
       exceptions = []
       matched_count = 0
   ```
8. Build the union of all keys:
   ```python
       all_keys = set(ledger_index.keys()) | set(settlement_index.keys())
   ```
9. Loop over every key and apply deterministic rules:
   - Key present in both sides → compare amounts with tolerance.
     - If difference ≤ tolerance → increment `matched_count`.
     - Else → create exception of type `"amount_mismatch"`.
   - Key only in ledger → create exception `"missing_in_settlement"`.
   - Key only in settlement → create exception `"missing_in_ledger"`.
10. For every mismatch:
    - Generate a new `exception_id` with `uuid.uuid4()`.
    - Set status = `"open"`.
    - Store amounts and difference when applicable.
    - Append to the `exceptions` list.
11. Write an initial audit event for each exception (`action="created"`, `actor_id="SYSTEM"`).
12. Add all exception records and audit events to the database session.
13. Commit the transaction:
    ```python
        db.commit()
    ```
14. Return the summary:
    ```python
        return {
            "batch_id": body.batch_id,
            "matched_count": matched_count,
            "exception_count": len(exceptions),
            "exceptions": exceptions
        }
    ```

**Output Example:**
```json
{
  "batch_id": "BAT-20261015-001",
  "matched_count": 1200,
  "exception_count": 48,
  "exceptions": [
    {
      "exception_id": "EXC-001",
      "type": "amount_mismatch",
      "status": "open",
      "ledger_amount": "100.00",
      "settlement_amount": "99.50",
      "difference": "0.50"
    }
  ]
}
```

**Workflow:**  
Client → POST /match → Load indexes → Deterministic comparison → Create exceptions + audit events → Commit → 200 OK

**Concepts Used:** Pure deterministic algorithm, Decimal tolerance, database transaction, audit writing

---

### 6.9 List Exceptions

**Endpoint:** `GET /exceptions`  
**Purpose:** Return a filterable and paginated list of exceptions.

**Input:** Optional query parameters – `status`, `type`, `batch_id`, `page`, `page_size`

**Detailed Process (Complete Implementation Guide)**

1. Create the endpoint in `src/routers/exceptions.py`:
   ```python
   @router.get("/exceptions")
   def list_exceptions(
       status: str | None = None,
       type: str | None = None,
       batch_id: str | None = None,
       page: int = 1,
       page_size: int = 20,
       db: Session = Depends(get_db)
   ):
   ```
2. Start a SQLAlchemy query on the exceptions table.
3. Apply filters only when the corresponding parameter is not None.
4. Calculate the total number of records after filtering.
5. Apply pagination:
   ```python
       offset = (page - 1) * page_size
       items = query.offset(offset).limit(page_size).all()
   ```
6. Return the response:
   ```python
       return {
           "total": total,
           "page": page,
           "page_size": page_size,
           "items": items
       }
   ```

**Workflow:**  
Client → GET /exceptions?status=open → Filter → Paginate → 200 OK

**Concepts Used:** Query parameter filtering, pagination, database querying

---

### 6.10 Get Single Exception Details

**Endpoint:** `GET /exceptions/{exception_id}`  
**Purpose:** Return the complete details of one exception.

**Input:** Path parameter `exception_id`

**Detailed Process (Complete Implementation Guide)**

1. Create the endpoint:
   ```python
   @router.get("/exceptions/{exception_id}")
   def get_exception(exception_id: str, db: Session = Depends(get_db)):
   ```
2. Query the exception by its unique `exception_id`.
3. If the record is not found:
   ```python
       raise HTTPException(status_code=404, detail="Exception not found")
   ```
4. Return the full exception object.

**Workflow:**  
Client → GET /exceptions/EXC-001 → Lookup → 200 OK or 404

**Concepts Used:** Path parameter binding, database lookup, HTTP 404

---

### 6.11 Record Disposition (Human Decision)

**Endpoint:** `POST /exceptions/{exception_id}/disposition`  
**Purpose:** Allow a human reviewer to approve, reject or rework an exception.  
This is the **only** endpoint that can change the final disposition.

**Input:**
```json
{
  "action": "approve",
  "actor_id": "REV-001",
  "reason": "Difference within operational tolerance"
}
```

**Detailed Process (Complete Implementation Guide)**

1. Define the request model in `src/models/exception.py`:
   ```python
   from pydantic import BaseModel
   from typing import Literal

   class DispositionRequest(BaseModel):
       action: Literal["approve", "reject", "rework"]
       actor_id: str
       reason: str
   ```
2. Create the endpoint:
   ```python
   @router.post("/exceptions/{exception_id}/disposition")
   def record_disposition(
       exception_id: str,
       body: DispositionRequest,
       db: Session = Depends(get_db)
   ):
   ```
3. Load the exception from the database. If not found, raise HTTP 404.
4. Validate the state transition:
   - Allowed only from status `"open"` or `"rework"`.
   - If the transition is not allowed, raise HTTP 409 Conflict.
5. Validate that `body.actor_id` is not empty.
6. Update the exception:
   - Set the new status according to `body.action`.
   - Update the timestamp.
7. Create a new audit event with:
   - A new UUID as `event_id`
   - `exception_id`
   - `from_status` and `to_status`
   - `actor_id`, `action`, `reason`, current timestamp
8. Add both the updated exception and the audit event to the session.
9. Commit the transaction and refresh the exception object.
10. Return the updated exception.

**Workflow:**  
Client → POST /exceptions/EXC-001/disposition → Validate actor + transition → Update status → Write audit → Commit → 200 OK

**Concepts Used:** Human-in-the-loop, finite-state machine, mandatory actor attribution, database transaction, immutable audit logging

---

### 6.12 Get Audit Trail

**Endpoint:** `GET /audit/{exception_id}`  
**Purpose:** Return the complete ordered history of every action performed on an exception.

**Input:** Path parameter `exception_id`

**Detailed Process (Complete Implementation Guide)**

1. Create the endpoint in `src/routers/audit.py`:
   ```python
   @router.get("/audit/{exception_id}")
   def get_audit_trail(exception_id: str, db: Session = Depends(get_db)):
   ```
2. Query all audit events that belong to the given `exception_id`.
3. Order the results by the `timestamp` column ascending.
4. Return the response:
   ```python
       return {
           "exception_id": exception_id,
           "events": events
       }
   ```

**Output Example:**
```json
{
  "exception_id": "EXC-001",
  "events": [
    {
      "event_id": "AUD-001",
      "timestamp": "2026-10-15T08:10:00Z",
      "actor_id": "SYSTEM",
      "action": "created",
      "from_status": null,
      "to_status": "open"
    },
    {
      "event_id": "AUD-002",
      "timestamp": "2026-10-15T08:25:00Z",
      "actor_id": "REV-001",
      "action": "approve",
      "from_status": "open",
      "to_status": "approved",
      "reason": "Difference within operational tolerance"
    }
  ]
}
```

**Workflow:**  
Client → GET /audit/EXC-001 → Query & sort events → 200 OK

**Concepts Used:** Database querying, chronological ordering, audit reconstructability

---

## 7. Common Concepts Used Across All Endpoints

| Concept                     | How to apply it                                              |
|----------------------------|--------------------------------------------------------------|
| `get_settings()`           | Call at the beginning of any function that needs configuration |
| `get_db()` dependency      | Always inject with `db: Session = Depends(get_db)`           |
| Pydantic models            | Use for both request bodies and response models              |
| HTTPException              | Use for 404, 409 and other error cases                       |
| Decimal                    | Never use `float` for money amounts                          |
| UUID                       | Generate for `batch_id`, `exception_id`, `event_id`          |
| `db.commit()`              | Call after all related writes inside a transaction           |
| Human decision boundary    | Only the disposition endpoint may change the final status    |

---

## 8. Suggested Implementation Order for Participants

1. Create project structure + `config.py` + `.env` + `database.py`
2. Implement Health endpoint
3. Implement Schema models + GET/POST schema endpoints
4. Implement Ledger ingest (most important learning step)
5. Implement Settlement ingest (reuse the same code)
6. Implement Control-totals endpoints
7. Implement Deterministic matcher
8. Implement Exception list + single exception detail
9. Implement Disposition endpoint + audit writing
10. Implement Audit retrieval endpoint


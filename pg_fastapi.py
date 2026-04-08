import fastapi as fa
from sqlalchemy.orm import Session
from pydantic import BaseModel
from main import Identifiers  # Import the model from main.py
from connectdb import get_session  # Import the session factory

app = fa.FastAPI()

# Pydantic models for request/response
class IdentifiersCreate(BaseModel):
    identifier_name: str
    description: str | None = None
    identifier_type: str | None = None

class IdentifiersResponse(BaseModel):
    identifier_name: str
    description: str | None
    identifier_type: str | None

class IdentifiersUpdate(BaseModel):
    identifier_name: str
    description: str | None = None
    identifier_type: str | None = None

# Dependency to get DB session
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

@app.get('/')
async def root():
    return {'message': 'Procter & Gamble Database API'}

@app.post("/identifiers/", response_model=IdentifiersResponse)
def create_identifier(identifier: IdentifiersCreate, db: Session = fa.Depends(get_db)):
    db_identifier = Identifiers(**identifier.model_dump())
    db.add(db_identifier)
    db.commit()
    db.refresh(db_identifier)
    return db_identifier

@app.get("/identifiers/", response_model=list[IdentifiersResponse])
def read_all_identifiers(db: Session = fa.Depends(get_db)):
    identifiers = db.query(Identifiers).all()
    return identifiers

@app.get("/identifiers/{identifier_name}", response_model=IdentifiersResponse)
def read_identifier(identifier_name: str, db: Session = fa.Depends(get_db)):
    identifier = db.query(Identifiers).filter(Identifiers.identifier_name == identifier_name).first()
    if identifier is None:
        raise fa.HTTPException(status_code=404, detail="Identifier not found")
    return identifier

@app.put("/identifiers/{identifier_name}", response_model=IdentifiersResponse)
def update_identifier(identifier_name: str, identifier: IdentifiersCreate, db: Session = fa.Depends(get_db)):
    db_identifier = db.query(Identifiers).filter(Identifiers.identifier_name == identifier_name).first()
    if db_identifier is None:
        raise fa.HTTPException(status_code=404, detail="Identifier not found")
    
    for key, value in identifier.model_dump().items():
        setattr(db_identifier, key, value)
    
    db.commit()
    db.refresh(db_identifier)
    return db_identifier

@app.patch("/identifiers/{identifier_name}", response_model=IdentifiersResponse)
def patch_identifier(identifier_name: str, identifier_update: IdentifiersUpdate, db: Session = fa.Depends(get_db)):
    db_identifier = db.query(Identifiers).filter(Identifiers.identifier_name == identifier_name).first()
    if db_identifier is None:
        raise fa.HTTPException(status_code=404, detail="Identifier not found")

    # Update only the fields that were provided
    if identifier_update.description is not None:
        db_identifier.description = identifier_update.description
    if identifier_update.identifier_type is not None:
        db_identifier.identifier_type = identifier_update.identifier_type

    db.commit()
    db.refresh(db_identifier)
    return db_identifier

@app.delete("/identifiers/{identifier_name}")
def delete_identifier(identifier_name: str, db: Session = fa.Depends(get_db)):
    db_identifier = db.query(Identifiers).filter(Identifiers.identifier_name == identifier_name).first()
    if db_identifier is None:
        raise fa.HTTPException(status_code=404, detail="Identifier not found")
    
    db.delete(db_identifier)
    db.commit()
    return {"detail": "Identifier deleted"}
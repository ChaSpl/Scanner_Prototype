from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.put("/persons/{person_id}", response_model=schemas.Person)
def update_person(person_id: int, update_data: schemas.PersonEditable, db: Session = Depends(get_db)):
    person = db.query(models.Person).filter(models.Person.id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    for field, value in update_data.model_dump().items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)
    return person

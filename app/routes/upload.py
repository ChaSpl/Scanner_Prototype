# app/routes/upload.py

import os
from typing import Generator
from fastapi import (
    APIRouter, Depends, UploadFile, File,
    BackgroundTasks, HTTPException, status
)
from sqlalchemy.orm import Session

from db.session import SessionLocal
from app.models import Document, Person, Visualization
from app.routes.auth import get_current_user
from app.services.parse_cv import parse_and_store
from app.services.generate_pdf import generate_cv_pdf
from app.services.plot_timeline_vertical import plot_timeline_and_save
from app.utils.audit_logger import logger

router = APIRouter(prefix="/documents", tags=["documents"])

# where uploaded files go
UPLOAD_DIR = os.path.abspath(os.path.join(os.getcwd(), "static", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for a request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def full_pipeline(
    document_id: int,
    fallback_email: str,
    user_id: str
):
    """
    Background task: parse the CV (using fallback_email if none
    is extracted), then generate PDF & timeline.
    """
    try:
        person_id = parse_and_store(document_id, fallback_email)
    except ValueError as e:
        logger.error(f"⚠️ full_pipeline aborted for doc {document_id}: {e}")
        return

    if not person_id:
        logger.error(f"⚠️ full_pipeline: no person for doc {document_id}")
        return

    # 1) generate PDF (attaching user_id)
    generate_cv_pdf(
        person_id=person_id,
        user_id=user_id,
        document_id=document_id
    )
    # 2) plot timeline
    plot_timeline_and_save(
        person_id=person_id,
        document_id=document_id
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Person = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    1) Save the uploaded file
    2) Create a Document(status='pending')
    3) Kick off full_pipeline in the background
    """
    # write file
    filename = f"{current_user.id}_{file.filename}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    with open(dest_path, "wb") as out:
        out.write(file.file.read())

    # record in DB
    doc = Document(
        title=file.filename,
        source_filename=dest_path,
        uploaded_by=str(current_user.id),
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # schedule the background task with fallback_email & user_id
    background_tasks.add_task(
        full_pipeline,
        doc.id,
        current_user.email,
        str(current_user.id),
    )

    return {"document_id": doc.id, "status": doc.status}


@router.get("/{doc_id}")
def get_document_status(
    doc_id: int,
    current_user: Person = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Poll to see when parsing (and auto–PDF/timeline) have completed.
    """
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": doc.id, "status": doc.status}


@router.post("/{doc_id}/generate_pdf")
def regenerate_pdf(
    doc_id: int,
    background_tasks: BackgroundTasks,
    current_user: Person = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually re‐generate the PDF once parsing is done.
    """
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status != "parsed":
        raise HTTPException(400, "Cannot generate PDF until document is parsed")

    person = db.query(Person).filter(Person.document_id == doc_id).first()
    if not person:
        raise HTTPException(500, "Parsed but no Person record found")

    background_tasks.add_task(
        generate_cv_pdf,
        person.id,
        str(current_user.id),
        document_id=doc_id
    )
    return {"document_id": doc_id, "pdf": "scheduled"}


@router.post("/{doc_id}/plot_timeline")
def regenerate_timeline(
    doc_id: int,
    background_tasks: BackgroundTasks,
    current_user: Person = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually re‐generate the timeline once parsing is done.
    """
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status != "parsed":
        raise HTTPException(400, "Cannot plot timeline until document is parsed")

    person = db.query(Person).filter(Person.document_id == doc_id).first()
    if not person:
        raise HTTPException(500, "Parsed but no Person record found")

    background_tasks.add_task(
        plot_timeline_and_save,
        person.id,
        document_id=doc_id
    )
    return {"document_id": doc_id, "timeline": "scheduled"}


@router.get("/{doc_id}/visualizations")
def list_visualizations(
    doc_id: int,
    current_user: Person = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return any generated visuals for this document.
    """
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    vizs = db.query(Visualization).filter_by(document_id=doc_id).all()
    return [
        {
            "id": v.id,
            "type": v.type,
            "file_path": v.file_path.replace("\\", "/")
        }
        for v in vizs
    ]

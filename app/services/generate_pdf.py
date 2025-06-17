# app/services/generate_pdf.py

import os
import re
from datetime import datetime
from fpdf import FPDF
from sqlalchemy.orm import joinedload

from db.session import SessionLocal
from app.models import (Person)
from app.utils.utils import sanitize
from app.utils.audit_logger import logger
from app.services.plot_timeline_vertical import register_visualization


# --- Helpers for date formatting --------------------------------------------

PROFICIENCY_ORDER = {
    "native": 0,
    "professional": 1,
    "intermediate": 2,
    "basic": 3,
    "none": 4
}

def format_date_with_precision(date_obj, precision):
    if not date_obj:
        return ""
    if precision == "day":
        return date_obj.strftime("%d/%m/%Y")
    if precision == "month":
        return date_obj.strftime("%m/%Y")
    if precision == "year":
        return date_obj.strftime("%Y")
    return ""

def format_date_range_with_precision(start, start_precision, end, end_precision, collapse_to_point=False):
    # if collapse_to_point=True, collapse identical start/end to a single date
    if collapse_to_point and start and (not end or start == end):
        return format_date_with_precision(start, start_precision)

    if start and end:
        if start == end and start_precision == end_precision:
            return format_date_with_precision(start, start_precision)
        return f"{format_date_with_precision(start, start_precision)} – {format_date_with_precision(end, end_precision)}"
    if start:
        return f"{format_date_with_precision(start, start_precision)} – present"
    if end:
        return f"until {format_date_with_precision(end, end_precision)}"
    return ""

def format_further_education_date_range(start, start_precision, end, end_precision):
    # Always collapse identical start/end for further education
    if not end or start == end:
        return format_date_with_precision(start, start_precision)
    return format_date_range_with_precision(start, start_precision, end, end_precision)

def sort_languages(langs):
    def key(lang):
        w = PROFICIENCY_ORDER.get((lang.proficiency_written or "").lower(), 99)
        s = PROFICIENCY_ORDER.get((lang.proficiency_spoken  or "").lower(), 99)
        return (w, s)
    return sorted(langs, key=key)

# --- PDF class --------------------------------------------------------------

class UniCV(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_font("Helvetica", size=11)

    def header(self):
        # Title + contact
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, getattr(self, "header_title", ""), ln=True)
        self.set_font("Helvetica", size=11)
        if hasattr(self, "header_contact") and self.header_contact:
            self.multi_cell(0, 8, self.header_contact)
        self.ln(2)
        # Draw a line
        self.set_draw_color(0)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        # No footer on page 1
        if self.page_no() == 1:
            return
        # Draw line
        self.set_y(-15)
        self.set_draw_color(0)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        # Page counter
        self.set_y(-10)
        self.set_font("Helvetica", size=9)
        page_str = str(self.page_no())
        full = f"{page_str}/{{nb}}"
        w = self.get_string_width(full)
        self.set_x((self.w - w) / 2)
        self.write(5, full)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, sanitize(title), ln=True)
        self.ln(1)
        self.set_font("Helvetica", size=11)

    def add_paragraph(self, text):
        self.multi_cell(0, 5, sanitize(text))
        self.ln(1)

# --- Main generator ---------------------------------------------------------

def generate_cv_pdf(
    person_id: int,
    output_path: str = None,
    user_id: str = "system",
    document_id: int | None = None,       # ← added parameter
):
    """
    Render CV PDF for a person and register it in the DB.
    """
    logger.info(f"📄 [PDF START] person_id={person_id} | doc_id={document_id} | by={user_id}")
    session = SessionLocal()
    try:
        person = session.get(
            Person, person_id,
            options=[
                joinedload(Person.educations),
                joinedload(Person.experiences),
                joinedload(Person.languages),
                joinedload(Person.certifications),
                joinedload(Person.awards),
                joinedload(Person.further_education),
                joinedload(Person.publications),
                joinedload(Person.personal_achievements),
                joinedload(Person.private_milestones),
            ]
        )
        if not person:
            msg = f"No Person #{person_id}"
            logger.error(f"❌ [PDF FAIL] {msg}")
            return

        # Decide output_path if not passed in
        if output_path is None:
            base = os.path.join(os.getcwd(), "PDFs_Test")
            os.makedirs(base, exist_ok=True)
            safe = re.sub(r"\W+", "_", (person.full_name or f"unknown_{person_id}").strip())
            output_path = os.path.join(base, f"UniCV_{safe}_{person_id}.pdf")
        

        # Start PDF
        pdf = UniCV()
        pdf.alias_nb_pages()
        pdf.header_title   = f"Standardized Curriculum Vitae for {person.full_name}"
        contact_parts = filter(None, [
            f"Email: {person.email}" if person.email else None,
            f"Phone: {person.phone}" if person.phone else None,
            f"LinkedIn: {person.linkedin}" if person.linkedin else None,
            f"GitHub: {person.github}" if person.github else None,
            f"Website: {person.website}" if person.website else None,
        ])
        pdf.header_contact = " | ".join(contact_parts)
        pdf.add_page()

        # Short Bio
        pdf.section_title("Short Bio")
        pdf.add_paragraph(person.short_bio or "No biography provided.")

        # Professional Experience
        if person.experiences:
            pdf.section_title("Professional Experience")
            for exp in sorted(person.experiences, key=lambda x: x.start_date or "", reverse=True):
                if not (exp.title and exp.company):
                    continue
                line = f"{exp.title} at {exp.company}"
                if exp.location:
                    line += f", {exp.location}"
                dr = format_date_range_with_precision(
                    exp.start_date, exp.start_date_precision,
                    exp.end_date,   exp.end_date_precision
                )
                if dr:
                    line += f" ({dr})"
                if exp.role_type:
                    line += f"\nRole: {exp.role_type}"
                if exp.role_description:
                    line += f"\n{exp.role_description}"
                pdf.add_paragraph(line)

        # — Education —
        if person.educations:
            pdf.section_title("Education")
            for edu in sorted(person.educations, key=lambda e: e.end_date or e.start_date or "", reverse=True):
                parts = []
                if edu.degree:          parts.append(edu.degree)
                if edu.field_of_study:  parts.append(f"in {edu.field_of_study}")
                if edu.institution:     parts.append(edu.institution)
                if not parts:
                    continue
                dr = format_date_range_with_precision(
                    edu.start_date, edu.start_date_precision,
                    edu.end_date,   edu.end_date_precision
                )
                pdf.add_paragraph(" ".join(parts) + (f" ({dr})" if dr else ""))

        # — Further Education —
        if person.further_education:
            pdf.section_title("Further Education")
            for fe in sorted(person.further_education, key=lambda f: f.end_date or f.start_date or "", reverse=True):
                if not fe.title:
                    continue
                parts = [fe.title]
                if fe.institution:
                    parts.append(f"– {fe.institution}")
                dr = format_further_education_date_range(
                    fe.start_date, fe.start_date_precision,
                    fe.end_date,   fe.end_date_precision
                )
                pdf.add_paragraph(" ".join(parts) + (f" ({dr})" if dr else ""))

        # — Certifications —
        if person.certifications:
            pdf.section_title("Certifications")
            for cert in person.certifications:
                if not cert.name:
                    continue
                line = cert.name + (f" – {cert.issuer}" if cert.issuer else "")
                dr   = format_date_range_with_precision(
                    cert.start_date, cert.start_date_precision,
                    cert.end_date,   cert.end_date_precision,
                    collapse_to_point=True
                )
                pdf.add_paragraph(f"{line}{f' ({dr})' if dr else ''}")

        # — Awards —
        if person.awards:
            pdf.section_title("Awards")
            for aw in person.awards:
                if not aw.name:
                    continue
                line = aw.name + (f" – {aw.awarded_by}" if aw.awarded_by else "")
                dr   = format_date_range_with_precision(
                    aw.start_date, aw.start_date_precision,
                    aw.end_date,   aw.end_date_precision,
                    collapse_to_point=True
                )
                pdf.add_paragraph(f"{line}{f' ({dr})' if dr else ''}")

        # — Languages —
        if person.languages:
            pdf.section_title("Languages")
            for lang in sort_languages(person.languages):
                if not lang.language:
                    continue
                pdf.add_paragraph(f"{lang.language} — Written: {lang.proficiency_written or 'N/A'}, "
                                  f"Spoken: {lang.proficiency_spoken or 'N/A'}")

        # — Publications —
        if person.publications:
            pdf.section_title("Publications")
            pubs = sorted(
                person.publications,
                key=lambda p: (
                    p.publication_date.year if p.publication_date else 0,
                    p.publication_date.month if p.publication_date and p.publication_date_precision in ("month","day") else 0
                ),
                reverse=True
            )
            for pub in pubs:
                parts = list(filter(None, [pub.title, pub.journal, pub.authors]))
                if not parts and not pub.publication_date:
                    continue
                dr = ""
                if pub.publication_date:
                    dr0 = format_date_with_precision(pub.publication_date, pub.publication_date_precision)
                    dr  = f" ({dr0})" if dr0 else ""
                pdf.add_paragraph(", ".join(parts) + dr)

        # — Personal Achievements —
        if person.personal_achievements:
            pdf.section_title("Personal Achievements")
            for ach in sorted(person.personal_achievements, key=lambda a: a.start_date or "", reverse=True):
                if not ach.achievement:
                    continue
                dr   = format_date_range_with_precision(
                    ach.start_date, ach.start_date_precision,
                    ach.end_date,   ach.end_date_precision
                )
                line = (f"{dr} – {ach.achievement}" if dr else ach.achievement)
                if ach.description:
                    line += f": {ach.description}"
                pdf.add_paragraph(line)

        # — Private Milestones —
        if person.private_milestones:
            pdf.section_title("Private Milestones")
            for ms in sorted(person.private_milestones, key=lambda m: m.start_date or "", reverse=True):
                if not ms.event:
                    continue
                dr   = format_date_range_with_precision(
                    ms.start_date, ms.start_date_precision,
                    ms.end_date,   ms.end_date_precision
                )
                line = (f"{ms.event} ({dr})" if dr else ms.event)
                if ms.description:
                    line += f": {ms.description}"
                pdf.add_paragraph(line)

        # Save and log
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf.output(output_path)

        # — register in DB if we know the document —
        if document_id is not None:
            register_visualization(
                document_id=document_id,
                relative_file_path=output_path,
                viz_type="pdf"
            )
            logger.info(f"✅ PDF visualization linked to document {document_id}: {output_path}")

        logger.info(
            f"📝 [PDF GENERATED] Person={person.full_name} | "
            f"ID={person.id} | Path={output_path} | by={user_id} | at={datetime.utcnow().isoformat()}"
        )

    except Exception as e:
        logger.exception(f"❌ [PDF ERROR] person_id={person_id} by={user_id} failed: {e}")
    finally:
        session.close()


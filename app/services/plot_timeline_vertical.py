# app/services/plot_timeline_vertical.py

import os
import sys
from datetime import date, datetime
import textwrap

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import matplotlib
matplotlib.use("Agg")

# force project root on PYTHONPATH so imports work if you run this file directly:
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from db.session import SessionLocal
from app.models import Person, Visualization
from app.utils.audit_logger import logger

# ───── helper funcs ─────

def normalize_date(dt, precision: str):
    """Round a date to year/month granularity for plotting."""
    if not dt:
        return None
    if precision == "year":
        return date(dt.year, 1, 1)
    if precision == "month":
        return date(dt.year, dt.month, 1)
    return dt  # day precision

def collect_timeline_events(person):
    events = []

    def add(obj, kind, title_attr, start_attr, end_attr, start_prec_attr, end_prec_attr):
        start = normalize_date(getattr(obj, start_attr), getattr(obj, start_prec_attr) or "day")
        end_raw = getattr(obj, end_attr)
        end = normalize_date(end_raw, getattr(obj, end_prec_attr) or "day")
        if not start:
            return
        # treat open-ended durations as “today” for bars
        if not end or start == end:
            end = date.today() if kind in ("Experience", "Education") else None
        events.append({
            "type": kind,
            "title": getattr(obj, title_attr) or "",
            "start_date": start,
            "end_date": end
        })

    # experiences & edu
    for exp in person.experiences:
        add(exp, "Experience",    "title",           "start_date", "end_date",
            "start_date_precision", "end_date_precision")
    for edu in person.educations:
        add(edu, "Education",     "degree",          "start_date", "end_date",
            "start_date_precision", "end_date_precision")
    # further ed, certs, awards
    for fe in person.further_education:
        add(fe, "Further Education", "title",       "start_date", "end_date",
            "start_date_precision",   "end_date_precision")
    for cert in person.certifications:
        add(cert, "Certification", "name",          "start_date", "end_date",
            "start_date_precision",   "end_date_precision")
    for award in person.awards:
        add(award, "Award",        "name",          "start_date", "end_date",
            "start_date_precision",   "end_date_precision")
    # publications are point events
    for pub in person.publications:
        pub_date = normalize_date(pub.publication_date, pub.publication_date_precision or "day")
        if pub_date:
            events.append({
                "type": "Publication",
                "title": pub.title or "",
                "start_date": pub_date,
                "end_date": None
            })
    # personal achievements & private milestones
    for pa in person.personal_achievements:
        add(pa, "Personal Ach.", "achievement",    "start_date", "end_date",
            "start_date_precision", "end_date_precision")
    for pm in person.private_milestones:
        add(pm, "Private Milestone", "event",      "start_date", "end_date",
            "start_date_precision",   "end_date_precision")

    logger.info(f"🧮 Collected {len(events)} timeline events for {person.full_name} ({person.id})")
    return events

# ───── main plotting + save ─────

def plot_timeline_and_save(person_id: int, document_id: int, save_dir: str = "static/timelines"):
    """
    1) Load Person
    2) Build event list
    3) Plot a simple vertical timeline
    4) Save PNG
    5) Register a Visualization linked to the given document_id
    """
    session = SessionLocal()
    try:
        person = session.get(Person, person_id)
        if not person:
            logger.error(f"❌ No person found ({person_id})")
            return

        events = collect_timeline_events(person)

        # bucket events for rows
        buckets = {
            "Experience": [],
            "Events":      [],   # certs / awards / further ed
            "Publications":[],
            "Personal":    []
        }
        for e in events:
            t = e["type"]
            if t in ("Experience","Education"):
                buckets["Experience"].append(e)
            elif t in ("Certification","Award","Further Education"):
                buckets["Events"].append(e)
            elif t == "Publication":
                buckets["Publications"].append(e)
            else:
                buckets["Personal"].append(e)

        rows = [k for k,v in buckets.items() if v]
        x_idx = {row:i for i,row in enumerate(rows)}

        fig, ax = plt.subplots(figsize=(max(12, len(events)*0.15), 8))
        for row in rows:
            base = x_idx[row]
            has_dur = any(e["end_date"] for e in buckets[row])
            offset = 0
            for ev in sorted(buckets[row], key=lambda x: x["start_date"]):
                s = ev["start_date"]; e = ev["end_date"]
                label = textwrap.fill(ev["title"], width=30)
                is_dur = bool(e)
                x = base + (offset*0.05 if is_dur and not row in ("Personal","Events") else 0)
                color = {
                    "Experience":"skyblue",
                    "Events":"orange",
                    "Publications":"green",
                    "Personal":"purple"
                }[row]
                if is_dur:
                    ax.plot([x,x],[s,e], color=color, linewidth=6, zorder=1)
                    mid = s + (e-s)/2
                    ax.text(x+0.05, mid, label, va="center", ha="left", fontsize=8)
                    if not row in ("Personal","Events"):
                        offset += 1
                else:
                    ax.plot([x],[s], marker="o", color=color, markersize=6, zorder=2)
                    ax.text(x+0.05, s, label, va="center", ha="left", fontsize=8)

        ax.set_xticks([x_idx[r] for r in rows])
        ax.set_xticklabels(rows)
        ax.yaxis.set_major_locator(mdates.YearLocator())
        ax.yaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.invert_yaxis()
        ax.set_title("Timeline")
        plt.tight_layout()

        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        fn = f"timeline_doc_{document_id}_{ts}.png"
        rel = os.path.join(save_dir, fn)
        plt.savefig(rel, dpi=300, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"📸 Saved timeline image {rel}")
        register_visualization(
            document_id=document_id,
            relative_file_path=rel,
            viz_type="timeline:png"
        )

    finally:
        session.close()

# ───── register ─────

def register_visualization(document_id: int, relative_file_path: str, viz_type: str="timeline:png"):
    session = SessionLocal()
    try:
        viz = Visualization(
            type=viz_type,
            file_path=relative_file_path.replace("\\","/"),
            document_id=document_id
        )
        session.add(viz)
        session.commit()
        logger.info(f"✅ Visualization linked to document {document_id}: {relative_file_path}")
    except Exception as e:
        logger.exception(f"❌ Could not register visualization for document {document_id}: {e}")
    finally:
        session.close()

# ───── command-line hook ─────

if __name__ == "__main__":
    pid = input("Person ID: ").strip()
    did = input("Document ID: ").strip()
    if pid.isdigit() and did.isdigit():
        plot_timeline_and_save(int(pid), int(did))
    else:
        print("Both must be numeric!")

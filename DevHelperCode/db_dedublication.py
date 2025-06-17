from sqlalchemy.orm import joinedload
from sqlalchemy import func
from db.session import SessionLocal
from app.models import (
    Person, Education, Language, Experience, Certification, Award,
    FurtherEducation, Publication, PersonalAchievement, PrivateMilestone
)

def deduplicate_persons():
    session = SessionLocal()
    try:
        # Step 1: Find duplicate emails
        duplicate_emails = (
            session.query(Person.email)
            .group_by(Person.email)
            .having(func.count(Person.id) > 1)
            .all()
        )
        duplicate_emails = [email[0] for email in duplicate_emails if email[0]]

        for email in duplicate_emails:
            persons = (
                session.query(Person)
                .filter(Person.email == email)
                .order_by(Person.id)
                .options(
                    joinedload(Person.educations),
                    joinedload(Person.languages),
                    joinedload(Person.experiences),
                    joinedload(Person.certifications),
                    joinedload(Person.awards),
                    joinedload(Person.further_education),
                    joinedload(Person.publications),
                    joinedload(Person.personal_achievements),
                    joinedload(Person.private_milestones),
                )
                .all()
            )

            canonical = persons[0]
            duplicates = persons[1:]

            for duplicate in duplicates:
                # Reassign related entries to the canonical person
                for entry in (
                    duplicate.educations + duplicate.languages + duplicate.experiences +
                    duplicate.certifications + duplicate.awards + duplicate.further_education +
                    duplicate.publications + duplicate.personal_achievements + duplicate.private_milestones
                ):
                    entry.person_id = canonical.id

                print(f"🗑️ Deleting duplicate person ID {duplicate.id} (email: {email})")
                session.delete(duplicate)

        session.commit()
        print("✅ Deduplication completed.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error during deduplication: {e}")
    finally:
        session.close()

# Run the deduplication
if __name__ == "__main__":
    deduplicate_persons()

# app/models.py
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Float, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base
 

# --- Core Entities ---

class Cluster(Base):
    __tablename__ = 'clusters'

    id = Column(Integer, primary_key=True)
    label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    embedding_ref = Column(Text, nullable=True)

    documents = relationship("Document", backref="cluster")
    visualizations = relationship("Visualization", back_populates="cluster")


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    source_filename = Column(String)
    uploaded_by = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum('pending', 'parsed', 'complete', 'error', name='status_enum'), default='pending')
    cluster_id = Column(Integer, ForeignKey('clusters.id'), nullable=True)

    llm_prompt = Column(Text, nullable=True)       
    llm_response = Column(Text, nullable=True)     

    extracted_fields = relationship("ExtractedField", back_populates="document")
    visualizations = relationship("Visualization", back_populates="document")
    person = relationship("Person", back_populates="document", uselist=False)



class ExtractedField(Base):
    __tablename__ = 'extracted_fields'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    field_name = Column(String)
    field_value = Column(String)
    confidence = Column(Float, nullable=True)

    document = relationship("Document", back_populates="extracted_fields")


class Visualization(Base):
    __tablename__ = 'visualizations'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'), nullable=True)
    type = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="visualizations")
    cluster = relationship("Cluster", back_populates="visualizations")


# --- CV Data Models ---

class Person(Base):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    github = Column(String, nullable=True)
    website = Column(String, nullable=True)
    short_bio = Column(Text, nullable=True)
    password_hash = Column(String, nullable=True)


    document_id = Column(Integer, ForeignKey('documents.id'))
    document = relationship("Document", back_populates="person")

    experiences = relationship("Experience", back_populates="person", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="person", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="person", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="person", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="person", cascade="all, delete-orphan")
    awards = relationship("Award", back_populates="person", cascade="all, delete-orphan")
    further_education = relationship("FurtherEducation", back_populates="person", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="person", cascade="all, delete-orphan")
    personal_achievements = relationship("PersonalAchievement", back_populates="person", cascade="all, delete-orphan")
    private_milestones = relationship("PrivateMilestone", back_populates="person", cascade="all, delete-orphan")



class Experience(Base):
    __tablename__ = 'experiences'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    person = relationship("Person", back_populates="experiences")

    title = Column(String)
    company = Column(String)
    location = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    is_current = Column(Integer, default=0)
    role_type = Column(String)
    role_description = Column(Text, nullable=True)


class Skill(Base):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    experience_id = Column(Integer, ForeignKey('experiences.id'), nullable=True)

    name = Column(String)
    confidence = Column(Float, nullable=True)
    source_context = Column(Text, nullable=True)

    person = relationship("Person", back_populates="skills")


class Education(Base):
    __tablename__ = 'educations'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))

    institution = Column(String)
    degree = Column(String)
    field_of_study = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    person = relationship("Person", back_populates="educations")


class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))

    language = Column(String)
    proficiency_written = Column(String, nullable=True)
    proficiency_spoken = Column(String, nullable=True)

    person = relationship("Person", back_populates="languages")


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"))

    name = Column(String)
    issuer = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    person = relationship("Person", back_populates="certifications")


class Award(Base):
    __tablename__ = "awards"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"))

    name = Column(String)
    awarded_by = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    person = relationship("Person", back_populates="awards")


class FurtherEducation(Base):
    __tablename__ = "further_educations"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"))

    title = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    institution = Column(String)

    person = relationship("Person", back_populates="further_education")


class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"))

    title = Column(String)
    journal = Column(String)
    authors = Column(Text)

    publication_date = Column(Date, nullable=True)
    publication_date_precision = Column(String, default="month")  # 'year', 'month', 'day'

    person = relationship("Person", back_populates="publications")



class PersonalAchievement(Base):
    __tablename__ = "personal_achievements"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"))

    achievement = Column(String)
    description = Column(Text)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")

    person = relationship("Person", back_populates="personal_achievements")


class PrivateMilestone(Base):
    __tablename__ = "private_milestones"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"))
    event = Column(String)
    description = Column(Text)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    start_date_precision = Column(String, default="day")  # 'year', 'month', 'day'
    end_date_precision = Column(String, default="day")


    person = relationship("Person", back_populates="private_milestones")


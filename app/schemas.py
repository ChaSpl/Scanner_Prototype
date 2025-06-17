#schemas.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List, Annotated
from datetime import date


# Define constraints with Annotated
NonEmptyStr = Annotated[str, constr(strip_whitespace=True, min_length=3)]
StrongPassword = Annotated[str, constr(min_length=8)]

# --- Experience ---
class Experience(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]
    is_current: Optional[int]
    role_type: Optional[str]
    role_description: Optional[str]

    model_config = {"from_attributes": True}


# --- Skill ---
class Skill(BaseModel):
    id: int
    name: str
    confidence: Optional[float]
    source_context: Optional[str]

    model_config = {"from_attributes": True}


# --- Education ---
class Education(BaseModel):
    id: int
    institution: str
    degree: str
    field_of_study: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Language ---
class Language(BaseModel):
    id: int
    language: str
    proficiency_written: Optional[str]
    proficiency_spoken: Optional[str]

    model_config = {"from_attributes": True}


# --- Certification ---
class Certification(BaseModel):
    id: int
    name: str
    issuer: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Award ---
class Award(BaseModel):
    id: int
    name: str
    awarded_by: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Further Education ---
class FurtherEducation(BaseModel):
    id: int
    title: str
    institution: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Publication ---
class Publication(BaseModel):
    id: int
    title: str
    journal: str
    authors: str
    publication_date: Optional[date]
    publication_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Personal Achievement ---
class PersonalAchievement(BaseModel):
    id: int
    achievement: str
    description: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}


# --- Private Milestone ---
class PrivateMilestone(BaseModel):
    id: int
    event: str
    description: str
    start_date: Optional[date]
    end_date: Optional[date]
    start_date_precision: Optional[str]
    end_date_precision: Optional[str]

    model_config = {"from_attributes": True}





# === Minimal Types ===
name_str = str
email_str = EmailStr  # Good practice for email validation

# --- PersonEditable (used for updates) ---
class PersonEditable(BaseModel):
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    website: Optional[str]
    short_bio: Optional[str]

    model_config = {"from_attributes": True}

# --- Person (API output) ---
class Person(PersonEditable):
    id: int

    experiences: List[Experience] = []
    skills: List[Skill] = []
    educations: List[Education] = []
    languages: List[Language] = []
    certifications: List[Certification] = []
    awards: List[Award] = []
    further_education: List[FurtherEducation] = []
    publications: List[Publication] = []
    personal_achievements: List[PersonalAchievement] = []
    private_milestones: List[PrivateMilestone] = []

    model_config = {"from_attributes": True}

# --- Registration Schema ---
class PersonRegistration(BaseModel):
    full_name: NonEmptyStr
    email: EmailStr

    model_config = {"from_attributes": True}

class RegisterInputStrict(BaseModel):  
    user: PersonRegistration
    password: StrongPassword

class RegisterResponse(BaseModel):
    message: str
    user_id: int
    access_token: Optional[str] = None




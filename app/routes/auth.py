# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.utils.audit_logger import logger
from app.database import get_db
from app import models
from app.schemas import (
    RegisterInputStrict,
    RegisterResponse,
    Person as PersonResponse,
    PersonEditable,
    Person
)
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DELTA
from app.security.token_store import is_token_revoked, revoke_token
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Person:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti: str = payload.get("jti")
        sub: str = payload.get("sub")
        if jti is None or sub is None or is_token_revoked(jti):
            raise credentials_exception

        user = db.query(models.Person).filter(models.Person.email == sub).first()
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception


# --- Routes ---

@router.post("/register", response_model=RegisterResponse, operation_id="register_user")
def register(input: RegisterInputStrict, db: Session = Depends(get_db)):
    normalized_email = input.user.email.lower().strip()
    password = input.password
    logger.info(f"🔐 Registration attempt for {normalized_email}")

    existing = db.query(models.Person).filter(models.Person.email == normalized_email).first()
    if existing:
        logger.warning(f"❌ Email already registered: {normalized_email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(password)
    user = models.Person(**{**input.user.model_dump(), "email": normalized_email})
    user.password_hash = hashed_pw

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=ACCESS_TOKEN_EXPIRE_DELTA
    )
    logger.info(f"✅ Registration successful: {user.id}")
    return {"message": "Registration successful", "user_id": user.id, "access_token": access_token}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.lower().strip()
    password = form_data.password
    logger.info(f"🔐 Login attempt for {email}")

    user = db.query(models.Person).filter(models.Person.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"❌ Login failed for {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=ACCESS_TOKEN_EXPIRE_DELTA
    )
    logger.info(f"✅ Login success for ID {user.id}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=Person)
def read_users_me(current_user: models.Person = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=PersonResponse, operation_id="update_me")
def update_me(
    updates: PersonEditable,
    db: Session = Depends(get_db),
    current_user: models.Person = Depends(get_current_user)
):
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    logger.info(f"✅ User ID {current_user.id} successfully updated")
    return current_user


@router.post("/logout")
def logout(
    current_user: models.Person = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    if jti:
        revoke_token(jti)
        logger.info(f"🔒 Token revoked for user ID {current_user.id}")
    return {"detail": "Logged out successfully"}

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Generator

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal
from models import User, Ticket
from mailer import (
    notify_ticket_created,
    notify_ticket_status_change,
    send_email,
    send_welcome_signup_email
)


def get_admin_emails(db: Session) -> list[str]:
    emails = set()
    env_admin = os.getenv("ADMIN_EMAIL")
    if env_admin:
        for e in env_admin.split(","):
            if e.strip():
                emails.add(e.strip())

    db_admins = db.query(User).filter(User.role == "admin").all()
    for a in db_admins:
        if a.email and a.email.strip():
            emails.add(a.email.strip())

    return list(emails)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


Base.metadata.create_all(bind=engine)
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing in .env")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(
    title="IT Support Ticketing API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Authentication settings
# -------------------------


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(
    user_id: int | None = None,
    role: str | None = None,
    data: dict | None = None
) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    if data is not None:
        payload = data.copy()
    else:
        payload = {
            "sub": str(user_id),
            "role": role
        }

    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if user is None:
            raise credentials_exception

        return user

    except (JWTError, ValueError):
        raise credentials_exception


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# -------------------------
# Schemas
# -------------------------

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TicketCreate(BaseModel):
    company: str
    issue_type: str
    location: str
    issue: str


class TicketUpdate(BaseModel):
    status: str | None = None
    remarks: str | None = None


class TicketResponse(BaseModel):
    id: int
    user_id: int
    company: str
    issue_type: str
    location: str
    issue: str
    status: str
    remarks: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Basic routes
# -------------------------

@app.get("/")
def home():
    return {
        "message": "IT Support Ticketing API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }


# -------------------------
# Authentication APIs
# -------------------------

@app.post("/auth/signup", response_model=UserResponse)
def signup(
    signup_data: SignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == signup_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=signup_data.name,
        email=signup_data.email,
        password_hash=hash_password(signup_data.password),
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Trigger welcome email to the newly registered employee
    background_tasks.add_task(
        send_welcome_signup_email,
        user_name=new_user.name,
        user_email=new_user.email
    )

    return new_user

@app.post("/auth/login")
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# -------------------------
# User APIs
# -------------------------

@app.get("/users", response_model=list[UserResponse])
def get_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return db.query(User).all()


# -------------------------
# Ticket APIs
# -------------------------

@app.post("/tickets", response_model=TicketResponse)
def create_ticket(
    ticket_data: TicketCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_ticket = Ticket(
        user_id=current_user.id,
        company=ticket_data.company,
        issue_type=ticket_data.issue_type,
        location=ticket_data.location,
        issue=ticket_data.issue
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Automatic email notification for both User and Admins
    admin_emails = get_admin_emails(db)
    background_tasks.add_task(
        notify_ticket_created,
        ticket_id=new_ticket.id,
        user_name=current_user.name,
        user_email=current_user.email,
        company=new_ticket.company,
        issue_type=new_ticket.issue_type,
        location=new_ticket.location,
        issue=new_ticket.issue,
        admin_emails=admin_emails
    )

    return new_ticket


@app.get("/tickets", response_model=list[TicketResponse])
def get_all_tickets(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@app.get("/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if (
        current_user.role != "admin"
        and ticket.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot access this ticket"
        )

    return ticket


@app.patch("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    old_status = ticket.status
    status_changed = (
        ticket_data.status is not None and ticket_data.status != old_status
    )
    remarks_changed = (
        ticket_data.remarks is not None and ticket_data.remarks != ticket.remarks
    )

    if ticket_data.status is not None:
        ticket.status = ticket_data.status

    if ticket_data.remarks is not None:
        ticket.remarks = ticket_data.remarks

    db.commit()
    db.refresh(ticket)

    # Automatic email notification for the employee when status or remarks change
    if (status_changed or remarks_changed) and ticket.user:
        background_tasks.add_task(
            notify_ticket_status_change,
            ticket_id=ticket.id,
            user_name=ticket.user.name,
            user_email=ticket.user.email,
            company=ticket.company,
            issue_type=ticket.issue_type,
            location=ticket.location,
            issue=ticket.issue,
            old_status=old_status,
            new_status=ticket.status,
            remarks=ticket.remarks
        )

    return ticket


class TestEmailRequest(BaseModel):
    to_email: EmailStr


@app.post("/admin/test-email")
def test_email(
    request: TestEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    background_tasks.add_task(
        send_email,
        to_email=request.to_email,
        subject="[IT Support Test] SMTP Notification Test",
        html_body="<p>This is a test notification from the IT Support Ticketing System.</p>",
        text_body="This is a test notification from the IT Support Ticketing System."
    )
    return {"message": f"Test email triggered for {request.to_email}"}

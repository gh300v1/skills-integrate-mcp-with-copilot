"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Cookie, FastAPI, HTTPException, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory student and session stores. These are intentionally simple for the
# demo application and reset whenever the server restarts.
users = {}
sessions = {}


class RegistrationRequest(BaseModel):
    email: str
    password: str
    full_name: str
    grade_level: str


class LoginRequest(BaseModel):
    email: str
    password: str


class VerificationRequest(BaseModel):
    token: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_school_for_email(email: str) -> str:
    domain = email.rsplit("@", 1)[1]
    if domain == "mergington.edu":
        return "Mergington High School"
    return domain


def hash_password(password: str, salt: str | None = None) -> str:
    password_salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), password_salt.encode(), 100_000
    ).hex()
    return f"{password_salt}${password_hash}"


def password_matches(password: str, stored_hash: str) -> bool:
    salt, expected_hash = stored_hash.split("$", 1)
    actual_hash = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual_hash, expected_hash)


def public_user(user: dict) -> dict:
    return {
        "email": user["email"],
        "full_name": user["full_name"],
        "grade_level": user["grade_level"],
        "school": user["school"],
        "email_verified": user["email_verified"],
    }


def get_current_user(session_token: str | None) -> dict:
    email = sessions.get(session_token)
    if not email or email not in users:
        raise HTTPException(status_code=401, detail="Please log in to continue")
    return users[email]


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_student(request: RegistrationRequest, response: Response):
    email = normalize_email(request.email)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not request.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required")
    if email in users:
        raise HTTPException(status_code=409, detail="An account already exists for this email")

    verification_token = secrets.token_urlsafe(24)
    users[email] = {
        "email": email,
        "full_name": request.full_name.strip(),
        "grade_level": request.grade_level.strip(),
        "school": get_school_for_email(email),
        "password_hash": hash_password(request.password),
        "email_verified": False,
        "verification_token": verification_token,
    }
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = email
    response.set_cookie("session_token", session_token, httponly=True, samesite="lax")
    return {
        "message": "Account created. Verify your email before managing organizations.",
        "user": public_user(users[email]),
        "verification_token": verification_token,
    }


@app.post("/auth/login")
def login_student(request: LoginRequest, response: Response):
    email = normalize_email(request.email)
    user = users.get(email)
    if not user or not password_matches(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = email
    response.set_cookie("session_token", session_token, httponly=True, samesite="lax")
    return {"message": "Logged in successfully", "user": public_user(user)}


@app.post("/auth/logout")
def logout_student(response: Response, session_token: str | None = Cookie(default=None)):
    if session_token:
        sessions.pop(session_token, None)
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
def get_profile(session_token: str | None = Cookie(default=None)):
    return public_user(get_current_user(session_token))


@app.post("/auth/verify-email")
def verify_email(request: VerificationRequest, session_token: str | None = Cookie(default=None)):
    user = get_current_user(session_token)
    if not hmac.compare_digest(request.token, user["verification_token"]):
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user["email_verified"] = True
    return {"message": "Email verified", "user": public_user(user)}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, session_token: str | None = Cookie(default=None)):
    """Sign up a student for an activity"""
    user = get_current_user(session_token)
    email = user["email"]
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, session_token: str | None = Cookie(default=None)):
    """Unregister a student from an activity"""
    user = get_current_user(session_token)
    email = user["email"]
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}

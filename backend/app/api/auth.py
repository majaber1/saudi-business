"""
Authentication & RBAC router: register, login, and profile.

Requires persistence (DATABASE_URL). In demo mode it returns 503 rather than
faking accounts, so nobody believes a login persisted when it did not.

Security note (public registration):
  ROLES is the *canonical* RBAC catalog used to seed the roles table so user
  foreign keys are always valid. It is NOT the set of roles a member of the
  public may self-assign. Public /auth/register only accepts
  PUBLIC_REGISTRATION_ROLES; privileged roles (admin, gov_reviewer) can never be
  obtained through public registration and must be provisioned through a
  controlled DB/bootstrap process or a future authenticated admin-only workflow.
"""
from __future__ import annotations

from typing import Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app import auth as security
from app.db import DB_ENABLED, SessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

# Canonical roles (key -> EN/AR label). Seeded on demand so user FKs are valid.
# NOTE: this is the full internal catalog, NOT the public-registration allowlist.
ROLES = {
    "entrepreneur": ("Entrepreneur", "رائد أعمال"),
    "consultant": ("Consultant", "مستشار"),
    "investor": ("Investor", "مستثمر"),
    "franchise_owner": ("Franchise Owner", "مانح امتياز"),
    "gov_reviewer": ("Government Reviewer", "مراجع حكومي"),
    "admin": ("Administrator", "مدير النظام"),
}

# Roles a member of the public may self-assign at registration time. Everything
# else in ROLES is privileged/internal and must never be reachable via the
# public endpoint.
PUBLIC_REGISTRATION_ROLES = frozenset(
    {"entrepreneur", "consultant", "investor", "franchise_owner"}
)
PRIVILEGED_ROLES = frozenset(set(ROLES) - PUBLIC_REGISTRATION_ROLES)  # admin, gov_reviewer

SUPPORTED_LOCALES = frozenset({"ar", "en"})
DEFAULT_ROLE = "entrepreneur"


def _normalize_email(email: str) -> str:
    """Canonicalize an email for storage and lookup so uniqueness is
    case-insensitive. RFC technically allows a case-sensitive local part, but
    for account identity we treat addresses case-insensitively (and trim
    surrounding whitespace) so "A@X.com" and "a@x.com" are the same account."""
    return email.strip().lower()


class RegisterIn(BaseModel):
    # Strict: reject any unexpected field (e.g. is_admin, is_staff, is_superuser,
    # permissions, is_active, organization_id, owner_id) instead of silently
    # ignoring it. Privilege can never be smuggled through the public payload.
    model_config = {"extra": "forbid"}

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=200)
    role_key: str = Field(default=DEFAULT_ROLE)
    locale: str = Field(default="ar")


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role_key: str
    locale: str


def _require_db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Auth requires persistence (DATABASE_URL not set).")
    return SessionLocal()


def _ensure_roles(db) -> None:
    """Seed the full canonical role catalog (including privileged roles) so user
    foreign keys are valid. This is unrelated to the public-registration
    allowlist: seeding admin/gov_reviewer here does NOT make them publicly
    self-assignable."""
    from app import models

    existing = {r.key for r in db.query(models.Role).all()}
    for key, (en, ar) in ROLES.items():
        if key not in existing:
            db.add(models.Role(key=key, name_en=en, name_ar=ar, permissions={}))
    db.commit()


def _audit(db, actor_id: Optional[int], action: str, entity: str, entity_id: Optional[int]) -> None:
    from app import models

    db.add(models.AuditLog(actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, meta={}))
    db.commit()


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn):
    from app import models

    # Public registration may only assign a public role. Reject privileged roles
    # explicitly (403) and unknown roles (422) BEFORE opening a DB session, so a
    # rejected request never creates a user row or an audit record.
    if data.role_key in PRIVILEGED_ROLES:
        raise HTTPException(status_code=403, detail="This role cannot be self-assigned")
    if data.role_key not in PUBLIC_REGISTRATION_ROLES:
        raise HTTPException(status_code=422, detail="Unknown role_key")
    if data.locale not in SUPPORTED_LOCALES:
        raise HTTPException(status_code=422, detail="Unsupported locale")

    email = _normalize_email(str(data.email))

    db = _require_db()
    try:
        _ensure_roles(db)
        if db.query(models.User).filter_by(email=email).first():
            raise HTTPException(status_code=409, detail="Email already registered")
        user = models.User(
            email=email,
            hashed_password=security.hash_password(data.password),
            full_name=data.full_name,
            role_key=data.role_key,  # validated public role only
            locale=data.locale,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        _audit(db, user.id, "user.register", "user", user.id)
        return UserOut(id=user.id, email=user.email, full_name=user.full_name,
                       role_key=user.role_key, locale=user.locale)
    finally:
        db.close()


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn):
    from app import models

    db = _require_db()
    try:
        user = db.query(models.User).filter_by(email=_normalize_email(str(data.email))).first()
        if not user or not security.verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")
        token = security.create_access_token(subject=user.id, extra={"role": user.role_key})
        _audit(db, user.id, "user.login", "user", user.id)
        return TokenOut(access_token=token)
    finally:
        db.close()


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)):
    from app import models

    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = security.decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Auth requires persistence")
    db = SessionLocal()
    try:
        user = db.get(models.User, int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        return UserOut(id=user.id, email=user.email, full_name=user.full_name,
                       role_key=user.role_key, locale=user.locale)
    finally:
        db.close()


def require_roles(*allowed: str):
    def _dep(user: UserOut = Depends(get_current_user)) -> UserOut:
        if user.role_key not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return _dep


@router.get("/me", response_model=UserOut)
def me(user: UserOut = Depends(get_current_user)):
    return user

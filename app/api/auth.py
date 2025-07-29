from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import InvalidCredentialsException, UserNotFoundException

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user.
    - Hashes the password before storing.
    - Checks if a user with the given email already exists.
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user_in.password)

    # Create new user
    new_user = User(email=user_in.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    print(f"User registered: {new_user.email}")
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Authenticates a user and returns a JWT access token.
    Uses OAuth2PasswordRequestForm for standard username/password login.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    # Create access token
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    print(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}

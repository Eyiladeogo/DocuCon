from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.db.models import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Retrieves the details of the currently authenticated user.
    Requires a valid JWT token.
    """
    print(f"Accessed /users/me for user: {current_user.email}")
    return current_user

from fastapi import APIRouter, Depends

from dependencies import require_admin
from models.user import User
from schemas.user_schemas import UserSchema

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me", response_model=UserSchema)
async def admin_me(current_admin: User = Depends(require_admin)):
    return current_admin

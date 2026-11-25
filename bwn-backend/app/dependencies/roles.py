from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user


def require_role(required_role: str):

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker
from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import get_database
from app.schemas.user import UserRegister, UserResponse
from app.utils.security import hash_password
from app.schemas.auth import UserLogin, TokenResponse
from app.utils.security import verify_password
from app.utils.jwt import create_access_token
from fastapi import Depends
from app.dependencies.auth import get_current_user
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user: UserRegister):
    database = get_database()
    users_collection = database["users"]

    existing_user = await users_collection.find_one(
        {"email": user.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user_document = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "role": "user",
    }

    try:
        result = await users_collection.insert_one(user_document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    return UserResponse(
        id=str(result.inserted_id),
        name=user.name,
        email=user.email,
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(user: UserLogin):
    database = get_database()
    users_collection = database["users"]

    # Find user by email
    existing_user = await users_collection.find_one(
        {"email": user.email}
    )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    is_password_valid = verify_password(
        user.password,
        existing_user["hashed_password"],
    )

    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT
    access_token = create_access_token(
        data={"sub": str(existing_user["_id"])}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
    )
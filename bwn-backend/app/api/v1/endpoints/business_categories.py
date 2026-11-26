from fastapi import APIRouter
from app.db.mongodb import get_database

router = APIRouter(
    prefix="/business-categories",
    tags=["Business Categories"],
)


@router.get("/")
async def get_business_categories():
    database = get_database()

    categories = await database["business_categories"].find(
        {"is_active": True}
    ).to_list(length=100)

    for category in categories:
        category["id"] = str(category.pop("_id"))

    return {
        "total": len(categories),
        "categories": categories,
    }

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_role
from app.schemas.business_category import BusinessCategoryCreate


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_business_category(
    category: BusinessCategoryCreate,
    current_user: dict = Depends(require_role("admin")),
):
    database = get_database()
    collection = database["business_categories"]

    existing = await collection.find_one({
        "name": category.name
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Category already exists",
        )

    category_document = {
        **category.model_dump(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    result = await collection.insert_one(category_document)

    return {
        "message": "Category created successfully",
        "category_id": str(result.inserted_id),
    }

from bson import ObjectId


@router.get("/{category_id}")
async def get_business_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid category ID",
        )

    database = get_database()

    category = await database["business_categories"].find_one({
        "_id": ObjectId(category_id),
        "is_active": True,
    })

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    category["id"] = str(category.pop("_id"))

    return category

@router.put("/{category_id}")
async def update_business_category(
    category_id: str,
    category: BusinessCategoryCreate,
    current_user: dict = Depends(require_role("admin")),
):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category ID")

    database = get_database()

    result = await database["business_categories"].update_one(
        {
            "_id": ObjectId(category_id),
            "is_active": True,
        },
        {
            "$set": category.model_dump()
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")

    return {"message": "Category updated successfully"}

@router.delete("/{category_id}")
async def delete_business_category(
    category_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid category ID",
        )

    database = get_database()

    result = await database["business_categories"].update_one(
        {
            "_id": ObjectId(category_id),
            "is_active": True,
        },
        {
            "$set": {"is_active": False}
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return {"message": "Category deactivated successfully"}
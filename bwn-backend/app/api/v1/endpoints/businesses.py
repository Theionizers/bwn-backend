from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import get_database
from app.dependencies.auth import get_current_user
from app.schemas.business import BusinessCreate
from fastapi import Body
router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_business(
    business: BusinessCreate,
    current_user: dict = Depends(get_current_user),
):
    database = get_database()
    businesses_collection = database["businesses"]

    business_document = {
        **business.model_dump(),
        "owner_id": current_user["_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_verified": False,
        "status": "pending",
    }

    result = await businesses_collection.insert_one(business_document)

    return {
        "message": "Business created successfully",
        "business_id": str(result.inserted_id),
    }

@router.get("/me")
async def get_my_businesses(
    current_user: dict = Depends(get_current_user),
):
    database = get_database()
    businesses_collection = database["businesses"]

    cursor = businesses_collection.find({
        "owner_id": current_user["_id"]
    })

    businesses = await cursor.to_list(length=100)

    for business in businesses:
        business["id"] = str(business.pop("_id"))
        business["owner_id"] = str(business["owner_id"])

    return {
        "total": len(businesses),
        "businesses": businesses,
    }

@router.put("/{business_id}")
async def update_business(
    business_id: str,
    updates: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(business_id):
        raise HTTPException(status_code=400, detail="Invalid business ID")

    allowed_fields = {
        "name", "description", "category", "subcategory",
        "phone", "email", "website", "address",
        "city", "state", "country", "pincode",
    }

    if not updates or not set(updates).issubset(allowed_fields):
        raise HTTPException(status_code=400, detail="Invalid update fields")

    database = get_database()
    businesses = database["businesses"]

    result = await businesses.update_one(
        {
            "_id": ObjectId(business_id),
            "owner_id": current_user["_id"],
        },
        {
            "$set": {
                **updates,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Business not found or you do not own it",
        )

    return {"message": "Business updated successfully"}
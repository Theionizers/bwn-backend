from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError
from app.dependencies.roles import require_role

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


@router.get("/pending")
async def get_pending_businesses(
    admin: dict = Depends(require_role("admin")),
):
    database = get_database()

    businesses = await database["businesses"].find(
        {"status": "pending"}
    ).to_list(length=100)

    for business in businesses:
        business["_id"] = str(business["_id"])
        business["owner_id"] = str(business["owner_id"])

    return {
        "total": len(businesses),
        "businesses": businesses,
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

@router.delete("/{business_id}")
async def delete_business(
    business_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(business_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid business ID",
        )

    database = get_database()

    result = await database["businesses"].delete_one({
        "_id": ObjectId(business_id),
        "owner_id": current_user["_id"],
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Business not found or you do not own it",
        )

    return {"message": "Business deleted successfully"}

@router.get("/search")
async def search_businesses(
    q: str | None = None,
    category: str | None = None,
    city: str | None = None,
    state: str | None = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination parameters",
        )

    filters = {
        "status": "active",
        "is_verified": True,
    }

    if q:
        filters["name"] = {"$regex": q, "$options": "i"}

    if category:
        filters["category"] = category

    if city:
        filters["city"] = {"$regex": f"^{city}$", "$options": "i"}

    if state:
        filters["state"] = {"$regex": f"^{state}$", "$options": "i"}

    database = get_database()
    collection = database["businesses"]

    skip = (page - 1) * limit

    cursor = collection.find(filters).skip(skip).limit(limit)
    businesses = await cursor.to_list(length=limit)

    total = await collection.count_documents(filters)

    for business in businesses:
        business["id"] = str(business.pop("_id"))
        business["owner_id"] = str(business["owner_id"])

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "businesses": businesses,
    }

@router.patch("/{business_id}/approve")
async def approve_business(
    business_id: str,
    admin: dict = Depends(require_role("admin")),
):
    if not ObjectId.is_valid(business_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid business ID",
        )

    database = get_database()

    result = await database["businesses"].update_one(
        {
            "_id": ObjectId(business_id),
            "status": "pending",
        },
        {
            "$set": {
                "status": "active",
                "is_verified": True,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Pending business not found",
        )

    return {"message": "Business approved successfully"}

@router.patch("/{business_id}/reject")
async def reject_business(
    business_id: str,
    admin: dict = Depends(require_role("admin")),
):
    if not ObjectId.is_valid(business_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid business ID",
        )

    database = get_database()

    result = await database["businesses"].update_one(
        {
            "_id": ObjectId(business_id),
            "status": "pending",
        },
        {
            "$set": {
                "status": "rejected",
                "is_verified": False,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Pending business not found",
        )

    return {"message": "Business rejected successfully"}

@router.get("/admin/all")
async def get_all_businesses(
    business_status: str | None = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(require_role("admin")),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination parameters",
        )

    allowed_statuses = {"pending", "active", "rejected"}

    filters = {}

    if business_status:
        if business_status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid business status",
            )

        filters["status"] = business_status

    database = get_database()
    collection = database["businesses"]

    skip = (page - 1) * limit

    cursor = collection.find(filters).skip(skip).limit(limit)
    businesses = await cursor.to_list(length=limit)

    total = await collection.count_documents(filters)

    for business in businesses:
        business["id"] = str(business.pop("_id"))
        business["owner_id"] = str(business["owner_id"])

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "businesses": businesses,
    }
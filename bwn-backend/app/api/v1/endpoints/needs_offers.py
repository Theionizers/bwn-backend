
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.mongodb import get_database
from app.dependencies.auth import get_current_user
from app.schemas.need_offer import NeedOfferCreate

router = APIRouter(
    prefix="/needs-offers",
    tags=["Needs & Offers"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_need_offer(
    post: NeedOfferCreate,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(post.business_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid business ID",
        )

    database = get_database()

    business = await database["businesses"].find_one({
        "_id": ObjectId(post.business_id),
        "owner_id": current_user["_id"],
    })

    if not business:
        raise HTTPException(
            status_code=404,
            detail="Business not found or you do not own it",
        )

    if business.get("status") != "active" or business.get("is_verified") is not True:
        raise HTTPException(
            status_code=403,
            detail="Only approved businesses can publish needs and offers",
        )

    post_document = {
        **post.model_dump(exclude={"business_id"}),
        "business_id": ObjectId(post.business_id),
        "owner_id": current_user["_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
    }

    result = await database["needs_offers"].insert_one(post_document)

    return {
        "message": "Need/Offer created successfully",
        "post_id": str(result.inserted_id),
    }


@router.get("/me")
async def get_my_needs_offers(
    current_user: dict = Depends(get_current_user),
):
    database = get_database()

    cursor = database["needs_offers"].find({
        "owner_id": current_user["_id"],
    }).sort("created_at", -1)

    posts = await cursor.to_list(length=100)

    for post in posts:
        post["id"] = str(post.pop("_id"))
        post["business_id"] = str(post["business_id"])
        post["owner_id"] = str(post["owner_id"])

    return {
        "total": len(posts),
        "posts": posts,
    }

@router.get("/{post_id}")
async def get_need_offer(
    post_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid post ID",
        )

    database = get_database()

    post = await database["needs_offers"].find_one({
        "_id": ObjectId(post_id),
        "is_active": True,
    })

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Need/offer post not found",
        )

    business = await database["businesses"].find_one({
        "_id": post["business_id"],
        "status": "active",
        "is_verified": True,
    })

    if not business:
        raise HTTPException(
            status_code=404,
            detail="Associated business not found",
        )

    post["id"] = str(post.pop("_id"))
    post["business_id"] = str(post["business_id"])
    post["owner_id"] = str(post["owner_id"])

    return post
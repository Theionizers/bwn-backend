from fastapi import APIRouter

from app.api.v1.endpoints import businesses
from app.api.v1.endpoints import business_categories

from app.api.v1.endpoints import auth, health
api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)

api_router.include_router(businesses.router)
api_router.include_router(business_categories.router)
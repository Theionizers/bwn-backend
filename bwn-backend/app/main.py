from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.router import api_router
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException

from app.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    create_database_indexes,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongodb()
    print("MongoDB connected successfully")

    await create_database_indexes()
    print("Database indexes created")

    yield

    # Shutdown
    await close_mongodb_connection()
    print("MongoDB connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )

# Register API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Welcome to BWNNext API"
    }

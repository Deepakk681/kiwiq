# PYTHONPATH=$(pwd):$(pwd)/services  poetry run python ./services/kiwi_app/main.py
# PYTHONPATH=$(pwd):$(pwd)/services  poetry run uvicorn main:app --app-dir services/kiwi_app --reload
import logging # Import logging
from contextlib import asynccontextmanager # Import asynccontextmanager
from fastapi import FastAPI
from global_config.logger import get_logger
from kiwi_app import auth
from kiwi_app.settings import settings # Import settings

# Get a logger instance for the main application
kiwi_logger = get_logger('kiwi_app')

tags_metadata = [
    {
        "name": "auth",
        "description": "Auth API endpoints including login, logout, register, verify email, verify password reset token, etc."
    },
    {
        "name": "organizations",
        "description": "Manage organizations. These endpoints allow you to read, update, and delete organizations, check or add/update membership, etc.",
        # "externalDocs": {
        #     "description": "Find more info",
        #     "url": "https://fastapi.tiangolo.com/"
        # }
    },
    {
        "name": "users",
        "description": "Manage users. These endpoints allow you to read your profile, update your profile etc.",
    },
    {
        "name": "admin",
        "description": "Admin API endpoints including creating roles, permissions, etc.",
    },
]

# --- Lifespan Context Manager --- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    # Startup logic
    kiwi_logger.info("Application starting up...")
    kiwi_logger.info(f"Log level set to: {settings.LOG_LEVEL.upper()}")
    # Add any other startup logic/logging here (e.g., initializing DB connections, loading models)
    # await init_db() # Ensure this is commented out if using Alembic
    yield
    # Shutdown logic
    kiwi_logger.info("Application shutting down...")
    # Add any cleanup logic here

# --- FastAPI App Setup --- #
# Pass the lifespan context manager to the FastAPI app
# TODO: replace with in production links for production!
app = FastAPI(
    title="KiwiQ Backend - Refactored Auth",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    )

# Include the authentication routes using the exposed router
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)

# ... rest of your app setup ...

@app.get("/")
async def root():
    kiwi_logger.debug("Root endpoint requested.") # Example debug log
    return {"message": "Welcome to KiwiQ API"} 


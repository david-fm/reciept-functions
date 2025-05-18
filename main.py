from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from api.routes import auth, users, receipts, categories, subscriptions, webhooks
from database import get_db
from models import get_categories_data
from core.config import settings

# Global variables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load categories from database

    print("Initializing categories...")

    # Get a database session
    db = next(get_db())
    try:
        # Initialize categories using your function
        settings.categories_data = get_categories_data(db)
        print(
            f"Categories loaded: {len(settings.categories_data.categories)} main categories found")
    except Exception as e:
        print(f"Error loading categories: {e}")
    finally:
        db.close()

    yield

    # Shutdown: Clear the categories data
    print("Clearing categories...")
    categories_data = None

# Create FastAPI application
app = FastAPI(
    title="Receipt Tracker API",
    description="API for tracking and analyzing receipts",
    version="1.0.0",
    lifespan=lifespan
)
app = FastAPI(lifespan=lifespan)

# Include routers - each with their own prefix
app.include_router(auth.router)
app.include_router(users.router, tags=["users"])
app.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
app.include_router(categories.router, prefix="/categories",
                   tags=["categories"])
app.include_router(subscriptions.router, tags=["subscriptions"])
app.include_router(webhooks.router, tags=["webhooks"])

# Root endpoint for health checks or documentation


@app.get("/")
async def get_index():
    return FileResponse('public/checkout.html')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

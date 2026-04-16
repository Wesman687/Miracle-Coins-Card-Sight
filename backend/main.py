from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Miracle Coins CoinSync Pro API",
    description="Admin-only system to manage coin and bullion inventory",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# CORS middleware — allow all origins (frontend may be on Vercel or localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure CORS headers are present even on error responses
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "*")
    headers = {"Access-Control-Allow-Origin": origin}
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)}, headers=headers)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin", "*")
    headers = {"Access-Control-Allow-Origin": origin}
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miracle-coins")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Security
security = HTTPBearer()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "miracle-coins-api", "code_version": "UPDATED_v5"}

# Test collections endpoint directly in main.py
@app.get("/api/v1/test-collections-direct")
async def test_collections_direct():
    """Test endpoint to get collections without authentication - direct in main.py"""
    import psycopg2
    
    try:
        # Direct database connection
        conn = psycopg2.connect(
            host='server.stream-lineai.com',
            port='5432',
            database='Miracle-Coins',
            user='Miracle-Coins',
            password='your_db_password_here'
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, description, color, shopify_collection_id FROM collections ORDER BY id LIMIT 5')
        collections = cursor.fetchall()
        
        result = []
        for collection in collections:
            result.append({
                "id": collection[0],
                "name": collection[1],
                "description": collection[2],
                "color": collection[3],
                "shopify_collection_id": collection[4]
            })
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Collections retrieved successfully",
            "count": len(result),
            "collections": result
        }
    except Exception as e:
        return {"error": str(e)}

# Include routers
from app.routers import pricing, images, listings, orders, ai_evaluation, ai_chat, task_management, pricing_agent, sales, inventory, financial, search, alerts, file_upload, bulk_operations, sku_system, audit_system, sync_system, consistency_system, storefront, auth_router
# Temporarily comment out collection imports to debug
from app.routers import collections
from app.routers import shopify_collections
# from app.routers import collection_metadata, collection_images, collection_analytics
from app.routers import coins
# Temporarily comment out coins_enhanced import to test coins router
# from app.routers import coins_enhanced

app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(coins.router, prefix="/api/v1", tags=["coins"])
app.include_router(storefront.router, prefix="/api/v1", tags=["storefront"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["pricing"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
app.include_router(listings.router, prefix="/api/v1", tags=["listings"])
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
app.include_router(ai_evaluation.router, prefix="/api/v1", tags=["ai-evaluation"])
app.include_router(ai_chat.router, prefix="/api/v1/ai-chat", tags=["ai-chat"])
app.include_router(task_management.router, prefix="/api/v1/task-management", tags=["task-management"])
app.include_router(pricing_agent.router, prefix="/api/v1/pricing-agent", tags=["pricing-agent"])
app.include_router(sales.router, prefix="/api/v1", tags=["sales"])
app.include_router(inventory.router, prefix="/api/v1", tags=["inventory"])
app.include_router(financial.router, prefix="/api/v1", tags=["financial"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(file_upload.router, prefix="/api/v1/files", tags=["file-upload"])
# Temporarily comment out coins_enhanced to test coins router
# app.include_router(coins_enhanced.router, prefix="/api/v1", tags=["coins-enhanced"])
app.include_router(bulk_operations.router, prefix="/api/v1", tags=["bulk-operations"])
# Temporarily comment out collection routers to debug
app.include_router(collections.router, prefix="/api/v1/collections", tags=["collections"])
app.include_router(sku_system.router, prefix="/api/v1", tags=["sku-management"])
app.include_router(audit_system.router, prefix="/api/v1", tags=["audit-management"])
app.include_router(sync_system.router, prefix="/api/v1", tags=["sync-management"])
app.include_router(consistency_system.router, prefix="/api/v1", tags=["consistency-management"])
app.include_router(shopify_collections.router, prefix="/api/v1/shopify", tags=["shopify-collections"])
# app.include_router(collection_metadata.router, prefix="/api/v1", tags=["collection-metadata"])
# app.include_router(collection_images.router, prefix="/api/v1", tags=["collection-images"])
# app.include_router(collection_analytics.router, prefix="/api/v1", tags=["collection-analytics"])

# Mount static files for uploaded images
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1270)

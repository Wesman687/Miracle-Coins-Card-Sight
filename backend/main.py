from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time
import logging
import logging.handlers
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = '%(asctime)s  %(levelname)-8s  %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def _file_handler(filename: str, level: int) -> logging.handlers.RotatingFileHandler:
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=10 * 1024 * 1024,   # 10 MB per file
        backupCount=10,
        encoding='utf-8',
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler

# Access logger  — every request
access_logger = logging.getLogger('miracle.access')
access_logger.setLevel(logging.INFO)
access_logger.addHandler(_file_handler('access.log', logging.INFO))
access_logger.propagate = False

# Error logger — 4xx/5xx + unhandled exceptions
error_logger = logging.getLogger('miracle.error')
error_logger.setLevel(logging.WARNING)
error_logger.addHandler(_file_handler('error.log', logging.WARNING))
error_logger.propagate = False

# App logger — general startup / info messages (also goes to console)
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)
logger = logging.getLogger(__name__)
logger.info('Miracle Coins backend starting up')

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Miracle Coins API",
    description="Storefront, inventory, and eBay management for Miracle Coins",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# CORS — allow all origins (frontend on Vercel + local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "-")
    msg = (
        f'{client_ip}  {request.method}  {request.url.path}'
        f'  {response.status_code}  {duration_ms:.1f}ms'
    )
    access_logger.info(msg)
    if response.status_code >= 500:
        error_logger.error(f'5xx  {msg}')
    elif response.status_code >= 400:
        error_logger.warning(f'4xx  {msg}')
    return response

# ---------------------------------------------------------------------------
# Error handlers (also ensure CORS headers on error responses)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "*")
    headers = {"Access-Control-Allow-Origin": origin}
    error_logger.exception(
        'Unhandled 500  %s %s  —  %s: %s',
        request.method, request.url.path, type(exc).__name__, exc,
    )
    return JSONResponse(status_code=500, content={"detail": str(exc)}, headers=headers)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin", "*")
    headers = {"Access-Control-Allow-Origin": origin}
    log = error_logger.warning if exc.status_code < 500 else error_logger.error
    log('HTTP %s  %s %s  —  %s', exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miracle-coins")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "miracle-coins-api"}

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from app.routers import (
    pricing, images, listings, orders, ai_evaluation, ai_chat,
    task_management, pricing_agent, sales, inventory, financial,
    search, alerts, file_upload, bulk_operations, sku_system,
    audit_system, sync_system, consistency_system, storefront, auth_router,
    collections, shopify_collections, coins,
)

app.include_router(auth_router.router,        prefix="/api/v1",             tags=["auth"])
app.include_router(coins.router,              prefix="/api/v1",             tags=["coins"])
app.include_router(storefront.router,         prefix="/api/v1",             tags=["storefront"])
app.include_router(pricing.router,            prefix="/api/v1/pricing",     tags=["pricing"])
app.include_router(images.router,             prefix="/api/v1/images",      tags=["images"])
app.include_router(listings.router,           prefix="/api/v1",             tags=["listings"])
app.include_router(orders.router,             prefix="/api/v1",             tags=["orders"])
app.include_router(ai_evaluation.router,      prefix="/api/v1",             tags=["ai-evaluation"])
app.include_router(ai_chat.router,            prefix="/api/v1/ai-chat",     tags=["ai-chat"])
app.include_router(task_management.router,    prefix="/api/v1/task-management", tags=["task-management"])
app.include_router(pricing_agent.router,      prefix="/api/v1/pricing-agent",   tags=["pricing-agent"])
app.include_router(sales.router,              prefix="/api/v1",             tags=["sales"])
app.include_router(inventory.router,          prefix="/api/v1",             tags=["inventory"])
app.include_router(financial.router,          prefix="/api/v1",             tags=["financial"])
app.include_router(search.router,             prefix="/api/v1",             tags=["search"])
app.include_router(alerts.router,             prefix="/api/v1",             tags=["alerts"])
app.include_router(file_upload.router,        prefix="/api/v1/files",       tags=["file-upload"])
app.include_router(bulk_operations.router,    prefix="/api/v1",             tags=["bulk-operations"])
app.include_router(collections.router,        prefix="/api/v1/collections", tags=["collections"])
app.include_router(sku_system.router,         prefix="/api/v1",             tags=["sku-management"])
app.include_router(audit_system.router,       prefix="/api/v1",             tags=["audit-management"])
app.include_router(sync_system.router,        prefix="/api/v1",             tags=["sync-management"])
app.include_router(consistency_system.router, prefix="/api/v1",             tags=["consistency-management"])
app.include_router(shopify_collections.router,prefix="/api/v1/shopify",     tags=["shopify-collections"])

# ---------------------------------------------------------------------------
# Static files (uploaded product images)
# ---------------------------------------------------------------------------
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1270)

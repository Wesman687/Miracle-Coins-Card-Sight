from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_orders():
    return {"message": "Orders endpoint - not implemented yet"}

@router.post("/")
async def create_order():
    return {"message": "Create order endpoint - not implemented yet"}
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_listings():
    return {"message": "Listings endpoint - not implemented yet"}

@router.post("/")
async def create_listing():
    return {"message": "Create listing endpoint - not implemented yet"}
from fastapi import APIRouter

router = APIRouter()

@router.post("/evaluate")
async def evaluate_coin():
    return {"message": "AI evaluation endpoint - not implemented yet"}

@router.get("/suggestions/{coin_id}")
async def get_suggestions(coin_id: int):
    return {"message": f"Get AI suggestions for coin {coin_id} - not implemented yet"}
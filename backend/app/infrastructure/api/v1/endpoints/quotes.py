from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.infrastructure.api.dependencies import get_db
from app.infrastructure.database.models.motivational_quote import MotivationalQuote
from pydantic import BaseModel

router = APIRouter()

class QuoteOut(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True

@router.get("/random", response_model=QuoteOut)
async def get_random_quote(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MotivationalQuote).order_by(func.random()).limit(1)
    )
    quote = result.scalars().first()
    
    if not quote:
        # Fallback if db is empty
        return {"id": 0, "text": "Cree en ti mismo y en lo que eres."}
        
    return quote

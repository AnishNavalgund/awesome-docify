from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import Example
from ..schemas import ExampleCreate, Example as ExampleSchema

router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/", response_model=List[ExampleSchema])
async def get_examples(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all examples"""
    result = await db.execute(select(Example).offset(skip).limit(limit))
    examples = result.scalars().all()
    return examples


@router.post("/", response_model=ExampleSchema)
async def create_example(example: ExampleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new example"""
    db_example = Example(**example.model_dump())
    db.add(db_example)
    await db.commit()
    await db.refresh(db_example)
    return db_example


@router.get("/{example_id}", response_model=ExampleSchema)
async def get_example(example_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific example by ID"""
    result = await db.execute(select(Example).filter(Example.id == example_id))
    example = result.scalar_one_or_none()
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return example 
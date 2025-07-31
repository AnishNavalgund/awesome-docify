from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExampleBase(BaseModel):
    """Base schema for Example"""

    title: str
    description: Optional[str] = None


class ExampleCreate(ExampleBase):
    """Schema for creating an Example"""

    pass


class ExampleUpdate(BaseModel):
    """Schema for updating an Example"""

    title: Optional[str] = None
    description: Optional[str] = None


class Example(ExampleBase):
    """Schema for Example response"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

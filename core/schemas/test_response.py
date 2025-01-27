# core/schemas/test_response.py

from uuid import UUID

from pydantic import BaseModel


class TestOut(BaseModel):
    id: UUID
    name: str
    description: str
    
    class Config:
        orm_mode = True

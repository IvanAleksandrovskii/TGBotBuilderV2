# core/schemas/custom_test.py

from typing import List, Optional
from pydantic import BaseModel, Field

from .base import BaseResponse


class Answer(BaseModel):
    text: str = Field(..., min_length=1)
    score: Optional[int]


class Question(BaseModel):
    question_text: str = Field(..., min_length=1)
    answers: Optional[List[Answer]] = None

    class Config:
        schema_extra = {
            "example": {
                "question_text": "What is the capital of France?",
                "answers": [
                    {"text": "Paris", "score": 1},
                    {"text": "Berlin", "score": 0},
                ],
            }
        }


class CustomTestBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    creator_id: int = Field(..., gt=0)
    allow_back: bool = True


class CustomTestCreate(CustomTestBase):
    questions: List[Question]

    class Config:
        schema_extra = {
            "example": {
                "name": "Sample Test",
                "description": "A test for demonstration purposes.",
                "creator_id": 12345,
                "allow_back": True,
                "questions": [
                    {
                        "question_text": "What is the capital of France?",
                        "answers": [
                            {"text": "Paris", "score": 1},
                            {"text": "Berlin", "score": 0},
                        ],
                    },
                    {
                        "question_text": "Describe your favorite hobby.",
                        "answers": None,
                    },
                ],
            }
        }


class CustomTestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    allow_back: Optional[bool]
    questions: Optional[List[Question]]


class CustomTestResponse(BaseResponse, CustomTestBase):
    questions: List[Question]

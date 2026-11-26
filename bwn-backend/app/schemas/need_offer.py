
from typing import Literal

from pydantic import BaseModel, Field


class NeedOfferCreate(BaseModel):
    business_id: str

    type: Literal["need", "offer"]

    title: str = Field(
        min_length=5,
        max_length=150,
    )

    description: str = Field(
        min_length=20,
        max_length=2000,
    )

    category: str = Field(
        min_length=2,
        max_length=100,
    )

    subcategory: str | None = Field(
        default=None,
        max_length=100,
    )


class NeedOfferUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=5,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        min_length=20,
        max_length=2000,
    )

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    subcategory: str | None = Field(
        default=None,
        max_length=100,
    )

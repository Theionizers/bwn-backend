from pydantic import BaseModel, Field
from typing import Optional


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: str
    subcategory: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    address: str
    city: str
    state: str
    country: str = "India"
    pincode: Optional[str] = None
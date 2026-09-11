"""Product request/response schemas."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    barcode: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = None
    category: str | None = None
    price_paise: int | None = Field(default=None, gt=0)
    store_id: uuid.UUID | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    barcode: str
    name: str
    brand: str | None
    category: str | None
    price_paise: int | None
    confidence_score: float
    source: str | None

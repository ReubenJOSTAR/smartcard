"""Session request/response schemas. See api/CLAUDE.md → Service Layer example."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    # store_id is intentionally not accepted here — MVP uses free-text store name
    # only (store_id/real Store selection lands in R3, see root CLAUDE.md §3).
    store_name_text: str = Field(min_length=1, max_length=255)
    budget_paise: int = Field(gt=0)


class SessionItemCreate(BaseModel):
    barcode: str = Field(min_length=1, max_length=32)
    quantity: int = Field(default=1, gt=0)


class SessionItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class SessionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    barcode: str
    name: str
    quantity: int
    estimated_price_paise: int
    line_total_paise: int


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_id: uuid.UUID | None
    store_name_text: str | None
    budget_paise: int
    status: str
    items: list[SessionItemResponse]
    estimated_total_paise: int
    created_at: datetime

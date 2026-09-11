"""History response schema. See api/CLAUDE.md → GET /v1/history."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistorySessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    store_name_text: str | None
    budget_paise: int
    status: str
    item_count: int
    estimated_total_paise: int
    created_at: datetime


class HistoryResponse(BaseModel):
    sessions: list[HistorySessionSummary]
    total: int
    limit: int
    offset: int

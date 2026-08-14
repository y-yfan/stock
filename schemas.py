from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool = True
    count: int = 0
    data: list[dict[str, Any]] = []
    message: str = ""
    source: str = ""

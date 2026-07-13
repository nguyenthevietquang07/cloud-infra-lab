from __future__ import annotations

import os

from fastapi import Header
from fastapi import HTTPException


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        return
    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

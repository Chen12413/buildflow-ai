from typing import Any

from pydantic import BaseModel


class ApiEnvelope(BaseModel):
    data: Any
    meta: Any = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Any = None


def success_response(data: Any, meta: Any = None) -> dict[str, Any]:
    return {"data": data, "meta": meta}

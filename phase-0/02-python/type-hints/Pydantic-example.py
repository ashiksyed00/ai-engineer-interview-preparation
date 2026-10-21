"""Pydantic v2 example: validated models for API-style data.

Setup:  pip install pydantic
Run:    python pydantic_example.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    model: str = "demo-model"
    messages: list[Message] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)

    @field_validator("model")
    @classmethod
    def model_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("model must not be blank")
        return v.strip()


def main() -> None:
    # 1. Valid data from a dict (e.g. parsed JSON). Pydantic coerces "0.5" -> 0.5
    req = ChatRequest.model_validate(
        {"messages": [{"role": "user", "content": "hi"}], "temperature": "0.5"}
    )
    print(req)
    print(req.temperature, type(req.temperature))

    # 2. Straight from a JSON string
    raw = '{"messages": [{"role": "user", "content": "hello"}], "max_tokens": 50}'
    print(ChatRequest.model_validate_json(raw))

    # 3. Invalid data -> clear, structured errors
    try:
        ChatRequest.model_validate(
            {"messages": [{"role": "admin", "content": ""}], "temperature": 5}
        )
    except ValidationError as exc:
        for err in exc.errors():
            print(err["loc"], "->", err["msg"])

    # 4. Back to dict / JSON
    print(req.model_dump())
    print(req.model_dump_json(exclude_none=True))


if __name__ == "__main__":
    main()
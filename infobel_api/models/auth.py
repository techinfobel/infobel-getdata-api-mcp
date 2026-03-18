"""Authentication token model."""

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    issued_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.expires_at is None:
            self.expires_at = self.issued_at + timedelta(seconds=self.expires_in)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TokenResponse":
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at  # type: ignore[operator]

    def needs_refresh(self, threshold_seconds: int) -> bool:
        time_until_expiry = (self.expires_at - datetime.now()).total_seconds()  # type: ignore[operator]
        return time_until_expiry <= threshold_seconds

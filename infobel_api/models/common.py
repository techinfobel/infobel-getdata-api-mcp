"""Shared types used across models."""

from pydantic import BaseModel, Field, ConfigDict


class CoordinateOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latitude: float = Field(alias="Latitude")
    longitude: float = Field(alias="Longitude")
    distance: int = Field(default=100, alias="Distance")

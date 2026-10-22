"""Shared primitives for strict decision contracts."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

type NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
type ArtifactIdStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[a-z][a-z0-9-]*-v\d+\.\d+\.\d+$",
    ),
]
type SemanticVersionStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^\d+\.\d+\.\d+$"),
]
type BoundedScore = Annotated[float, Field(ge=0.0, le=1.0)]


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

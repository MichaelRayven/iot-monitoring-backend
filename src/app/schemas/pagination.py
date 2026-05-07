from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PaginationParams(BaseModel):
    """Pagination parameters for query validation"""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(
        100, ge=1, le=1000, description="Maximum number of records to return"
    )
    search: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Search term"
    )

    model_config = ConfigDict(extra="forbid")

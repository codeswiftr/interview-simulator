"""Rate limit event model for PostgreSQL-backed rate limiting."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class RateLimitEvent(SQLModel, table=True):
    """Persisted rate limit event for sliding-window rate limiting.

    Each row represents one accepted request.  Old rows are periodically
    cleaned up by the middleware so the table stays small.
    """

    __tablename__ = "rate_limit_events"

    id: int | None = Field(default=None, primary_key=True)
    # ip:path  or  apikey:<prefix>:path  or  user:<id>:path
    key: str = Field(index=True)
    window_start: datetime
    count: int = Field(default=1)

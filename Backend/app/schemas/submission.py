from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SubmissionBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="text", pattern="^(text|image|video|audio)$")
    text_content: Optional[str] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    source_identifier: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    workspace_id: str
    batch_id: Optional[str] = None


class SubmissionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    source_identifier: Optional[str] = None


class SubmissionRead(SubmissionBase):
    id: str
    workspace_id: str
    submitter_id: Optional[str] = None
    batch_id: Optional[str] = None
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

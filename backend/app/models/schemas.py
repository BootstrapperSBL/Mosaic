from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UploadType(str, Enum):
    IMAGE = "image"
    URL = "url"
    TEXT = "text"


class SearchProvider(str, Enum):
    TAVILY = "tavily"
    SERPER = "serper"


class UploadRequest(BaseModel):
    type: UploadType
    content: str  # Base64 for image, URL string, or plain text
    user_id: str


class UploadResponse(BaseModel):
    id: str
    type: UploadType
    created_at: datetime
    status: str


class AnalysisResult(BaseModel):
    upload_id: str
    visual_description: Optional[str] = None
    extracted_text: Optional[str] = None
    intent_analysis: Dict[str, Any]
    keywords: List[str]
    interest_tags: List[str]
    created_at: datetime


class RecommendationTile(BaseModel):
    id: str
    title: str
    description: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    source: str
    relevance_score: float
    tile_type: str  # "knowledge", "product", "location", "tutorial", etc.


class RecommendationResponse(BaseModel):
    analysis_id: str
    tiles: List[RecommendationTile]
    generated_at: datetime


class UserFeedback(BaseModel):
    recommendation_id: str
    action: str  # "keep" or "discard"
    user_id: str


class HistoryItem(BaseModel):
    id: str
    type: UploadType
    content_preview: str
    analysis_summary: Optional[str] = None
    recommendation_count: int
    created_at: datetime


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


class AsyncTaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

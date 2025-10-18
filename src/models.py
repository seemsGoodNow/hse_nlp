from typing import List, Optional
from pydantic import BaseModel


class LawLink(BaseModel):
    law_id: Optional[int] = None
    article: Optional[str] = None
    point_article: Optional[str] = None
    subpoint_article: Optional[str] = None


class LinksResponse(BaseModel):
    links: List[LawLink]


class TextRequest(BaseModel):
    text: str


class RawLawLink(BaseModel):
    subpoint_article: Optional[str] = None
    point_article: Optional[str] = None
    article: Optional[str] = None
    law_source: Optional[str] = None

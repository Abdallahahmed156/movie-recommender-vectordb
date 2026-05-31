from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str
    n_results: int = 6

class MovieResult(BaseModel):
    id: str
    title: str
    overview: str
    genres: str
    release_date: str
    vote_average: float
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    similarity_score: float
    reason: str

class SearchResponse(BaseModel):
    results: list[MovieResult]
    query: str
    total: int
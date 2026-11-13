from pydantic import BaseModel, Field


class University(BaseModel):
    name: str
    country: str
    alpha_two_code: str | None = None
    state_province: str | None = Field(default=None, alias="state-province")
    domains: list[str] = []
    web_pages: list[str] = []

    model_config = {"populate_by_name": True}


class SearchResponse(BaseModel):
    source: str
    count: int
    query: dict[str, str | None]
    results: list[University]

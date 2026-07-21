import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "funding-engine"))
from matcher import match  # noqa: E402

router = APIRouter(prefix="/funding", tags=["funding"])


class FundingMatchRequest(BaseModel):
    industry: str = Field(..., min_length=1)
    stage: str = Field(default="idea", description="idea | mvp | early_revenue | growth")
    has_mvp: bool = False
    has_technical_team: bool = True


@router.post("/match")
def match_funding(req: FundingMatchRequest):
    return match(
        industry=req.industry,
        stage=req.stage,
        has_mvp=req.has_mvp,
        has_technical_team=req.has_technical_team,
    )

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubjectGraphNode(BaseModel):
    id: str
    kind: Literal["subject"]
    phone: str
    level: str
    score: int
    report_count: int
    last_activity: datetime | None


class AccountGraphNode(BaseModel):
    id: str
    kind: Literal["account"]
    phone: str
    level: str
    score: int
    report_count: int
    last_activity: datetime | None


class ReportGraphNode(BaseModel):
    id: str
    kind: Literal["report"]
    report_id: int
    created_at: datetime | None
    scam_type: str
    summary: str


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str


class RecipientGraph(BaseModel):
    phone: str
    reports_total: int
    nodes: list[SubjectGraphNode | AccountGraphNode | ReportGraphNode]
    edges: list[GraphEdge]

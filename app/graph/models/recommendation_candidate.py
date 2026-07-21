from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticCandidateRecord:
    code: str
    score: float


@dataclass(frozen=True)
class MatchedByRecord:
    source_labels: list[str]
    source_code: str
    suggestion_mode: str
    reason: str


@dataclass(frozen=True)
class RecommendationCandidateRecord:
    code: str
    name: str
    conditional_text: str
    description: str
    action_type: str
    target_type: str
    suggestion_level: str
    default_timing: str
    default_rank: int | None = None
    vector_score: float | None = None
    matched_by: list[MatchedByRecord] = field(default_factory=list)
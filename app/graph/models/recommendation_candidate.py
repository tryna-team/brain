from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecommendationCandidateRecord:
    template_id: str
    title: str
    base_item_type: str
    offset_days: int | None
    score: int
    source_relations: list[str] = field(default_factory=list)
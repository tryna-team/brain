from enum import StrEnum

class PipelineStep(StrEnum):
    CONTEXT = "context"
    CANDIDATES = "candidates"
    # REFINED_ITEMS = "refined_items"
    # VALIDATED_ITEMS = "validated_items"

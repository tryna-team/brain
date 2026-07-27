from typing import Literal, get_args

# API 요청/응답 및 내부 파이프라인 DTO에서 공통으로 사용하는 문자열 타입 정의
SourceType = Literal[
    "user_natural_language",
    "user_manual_edit",
]

ConfidenceLevel = Literal[
    "low", 
    "medium",
    "high", 
    "unknown"
]

DateSource = Literal[
    "explicit",
    "relative_expression",
    "default_today",
]

DATE_SOURCE_VALUES = set(get_args(DateSource))

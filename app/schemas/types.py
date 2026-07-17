from typing import Literal

# API 요청/응답 및 내부 파이프라인 DTO에서 공통으로 사용하는 문자열 타입 정의
SourceType = Literal[
    "USER_NATURAL_LANGUAGE",
    "USER_MANUAL_EDIT",
    "EXTERNAL_CALENDAR",
    "EXTERNAL_BASED_INTERNAL",
]

ConfidenceLevel = Literal[
    "low", 
    "medium",
    "high", 
    "unknown"
]

from typing import Literal, get_args

# 파싱, 실행 항목 추천 로직에서 공통으로 사용하는 문자열 타입 정의
DateSource = Literal[
    "EXPLICIT",
    "RELATIVE_EXPRESSION",
    "DEFAULT_TODAY",
]

DATE_SOURCE_VALUES = set(get_args(DateSource))

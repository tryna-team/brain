import re
from dataclasses import dataclass
from datetime import date, timedelta

try:
    from kiwipiepy import Kiwi
except ImportError:
    Kiwi = None


WEEKDAY_INDEX = {
    "월요일": 0,
    "화요일": 1,
    "수요일": 2,
    "목요일": 3,
    "금요일": 4,
    "토요일": 5,
    "일요일": 6,
}

DATE_PATTERNS = [
    # 한글 날짜 표현을 처리합니다: 2026년 8월 22일, 8월 22일.
    re.compile(r"(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:에)?"),
    re.compile(r"(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:에)?"),
    # 숫자 날짜 표현을 처리합니다: 2026-08-22, 2026/08/22, 2026.08.22, 08/22.
    re.compile(r"(?P<year>\d{4})[-/.](?P<month>\d{1,2})[-/.](?P<day>\d{1,2})"),
    re.compile(r"(?<![\d/.-])(?P<month>\d{1,2})/(?P<day>\d{1,2})(?![\d/.-])"),
]

# 오전/오후, 반, 분, 쯤/경이 포함된 시간 표현을 처리합니다.
TIME_PATTERN = re.compile(
    r"(?:(?P<period>오전|오후|저녁|아침|밤|새벽|점심|낮)(?:에)?\s*)?"
    r"(?P<hour>\d{1,2})시"
    r"(?:\s*(?P<half>반)|\s*(?P<minute>\d{1,2})분)?"
    r"(?:\s*(?:쯤|경))?"
)

AMBIGUOUS_TIME_WORDS = {
    "오전에": "morning",
    "오전": "morning",
    "아침에": "morning",
    "아침": "morning",
    "오후에": "afternoon",
    "오후": "afternoon",
    "낮에": "afternoon",
    "낮": "afternoon",
    "저녁에": "evening",
    "저녁": "evening",
    "밤에": "evening",
    "밤": "evening",
    "새벽에": "dawn",
    "새벽": "dawn",
}

PLACE_PATTERN = re.compile(
    # 앞쪽 제목 단어가 장소 후보에 섞이지 않도록 경계를 둡니다.
    r"(?:^|\s)(?P<place>"
    r"[가-힣A-Za-z0-9]+역\s+\d+번\s+출구"
    r"|(?:서울|부산|수원|대구|대전|광주|인천|제주|강남|홍대|신촌|건대|잠실|판교)\s+(?:[가-힣A-Za-z0-9]+(?:역|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)"
    r"|(?:[가-힣A-Za-z0-9]+(?:역|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)"
    r"|[가-힣A-Za-z0-9]+(?:시|군|구|동|읍|면|리)"
    r"|부산|서울|수원|대구|대전|광주|인천|제주"
    r")(?:에서|에)"
)


EMBEDDING_POS_PREFIXES = ("N",)
EMBEDDING_POS_TAGS = {"SL", "SN"}
EMBEDDING_STOP_WORDS = {"것", "수", "등"}
KIWI = Kiwi() if Kiwi else None


@dataclass(frozen=True)
class ParsedEvent:
    """룰베이스 파싱 결과를 서비스 계층에 전달하기 위한 일정 후보 DTO입니다."""

    source_text: str
    start_date: str | None
    end_date: str | None
    start_time: str | None
    end_time: str | None
    place_candidate: str | None
    to_embedding: list[str]
    is_past_date: bool
    is_time_ambiguous: bool


@dataclass(frozen=True)
class ExtractedValue:
    """추출된 후보값과 원문에서 제거해야 할 텍스트, 보정 플래그를 함께 담습니다."""

    value: str | None
    text: str | None = None
    removable_texts: tuple[str, ...] = ()
    is_past: bool = False
    is_ambiguous: bool = False


@dataclass(frozen=True)
class ExtractedTime:
    """시작/종료 시간 후보와 원문에서 제거할 시간 표현을 함께 담습니다."""

    start_value: str | None = None
    end_value: str | None = None
    text: str | None = None
    is_ambiguous: bool = False


def parse_event_text(source_text: str) -> ParsedEvent:
    """사용자 원문을 날짜/시간/장소 후보와 임베딩 키워드로 변환합니다."""
    normalized_text = _normalize_spaces(source_text)

    extracted_date = _extract_date(normalized_text)
    extracted_time = _extract_time(normalized_text)
    extracted_place = _extract_place(
        source_text=normalized_text,
        removable_texts=[
            *extracted_date.removable_texts,
            extracted_time.text,
        ],
    )
    to_embedding = _build_to_embedding(
        source_text=normalized_text,
        removable_texts=[
            *extracted_date.removable_texts,
            extracted_time.text,
            extracted_place.text,
        ],
    )

    return ParsedEvent(
        source_text=normalized_text,
        start_date=extracted_date.value,
        end_date=None,
        start_time=extracted_time.start_value,
        end_time=extracted_time.end_value,
        place_candidate=extracted_place.value,
        to_embedding=to_embedding,
        is_past_date=extracted_date.is_past,
        is_time_ambiguous=extracted_time.is_ambiguous,
    )


def _extract_date(source_text: str) -> ExtractedValue:
    """절대 날짜, 상대 날짜, 요일 표현 중 원문에서 가장 먼저 나온 날짜 후보를 반환합니다."""
    today = date.today()
    candidates: list[tuple[int, ExtractedValue]] = []
    removable_texts: list[str] = []

    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(source_text):
            year = int(match.groupdict().get("year") or today.year)
            month = int(match.group("month"))
            day = int(match.group("day"))

            try:
                parsed_date = date(year, month, day)
            except ValueError:
                continue

            removable_texts.append(match.group(0))
            candidates.append(
                (
                    match.start(),
                    ExtractedValue(
                        value=parsed_date.isoformat(),
                        text=match.group(0),
                        is_past=parsed_date < today,
                    ),
                )
            )

    relative_dates = {
        "오늘": today,
        "내일": today + timedelta(days=1),
        "모레": today + timedelta(days=2),
    }
    for text, parsed_date in relative_dates.items():
        index = source_text.find(text)
        if index != -1:
            removable_texts.append(text)
            candidates.append(
                (
                    index,
                    ExtractedValue(value=parsed_date.isoformat(), text=text),
                )
            )

    for weekday_text, weekday in WEEKDAY_INDEX.items():
        for relative_week_text, week_offset in (
            (f"이번 {weekday_text}", 0),
            (f"다음 {weekday_text}", 1),
            (f"다다음 {weekday_text}", 2),
            (f"다다음주 {weekday_text}", 2),
            (f"다다음 주 {weekday_text}", 2),
        ):
            relative_week_index = source_text.find(relative_week_text)
            if relative_week_index != -1:
                parsed_date = _this_weekday(today + timedelta(days=7 * week_offset), weekday)
                removable_texts.append(relative_week_text)
                candidates.append(
                    (
                        relative_week_index,
                        ExtractedValue(
                            value=parsed_date.isoformat(),
                            text=relative_week_text,
                            is_past=parsed_date < today,
                        ),
                    )
                )

        for this_week_text in (
            f"이번 주 {weekday_text}",
            f"이번주 {weekday_text}",
            f"요번 주 {weekday_text}",
            f"요번주 {weekday_text}",
        ):
            this_week_index = source_text.find(this_week_text)
            if this_week_index != -1:
                parsed_date = _this_weekday(today, weekday)
                removable_texts.append(this_week_text)
                candidates.append(
                    (
                        this_week_index,
                        ExtractedValue(
                            value=parsed_date.isoformat(),
                            text=this_week_text,
                            is_past=parsed_date < today,
                        ),
                    )
                )

        for next_week_text in (
            f"다음 주 {weekday_text}",
            f"다음주 {weekday_text}",
            f"담 주 {weekday_text}",
            f"담주 {weekday_text}",
        ):
            next_week_index = source_text.find(next_week_text)
            if next_week_index != -1:
                parsed_date = _this_weekday(today + timedelta(days=7), weekday)
                removable_texts.append(next_week_text)
                candidates.append(
                    (
                        next_week_index,
                        ExtractedValue(value=parsed_date.isoformat(), text=next_week_text),
                    )
                )

        weekday_index = source_text.find(weekday_text)
        if weekday_index != -1:
            parsed_date = _next_weekday(today, weekday)
            weekday_match = re.search(rf"{weekday_text}(?:에)?", source_text)
            removable_text = weekday_match.group(0) if weekday_match else weekday_text
            removable_texts.append(removable_text)
            candidates.append(
                (
                    weekday_index,
                    ExtractedValue(value=parsed_date.isoformat(), text=removable_text),
                )
            )

    if candidates:
        selected = min(candidates, key=lambda candidate: candidate[0])[1]
        return ExtractedValue(
            value=selected.value,
            text=selected.text,
            removable_texts=_dedupe_longest_first(removable_texts),
            is_past=selected.is_past,
            is_ambiguous=selected.is_ambiguous,
        )

    return ExtractedValue(value=None)


def _extract_time(source_text: str) -> ExtractedTime:
    """명확한 시간은 HH:mm으로, 시간 범위는 시작/종료 후보로 나누어 반환합니다."""
    matches = list(TIME_PATTERN.finditer(source_text))
    if matches:
        start_match = matches[0]
        start_value = _format_time_match(start_match)
        if start_value is not None:
            end_match = _find_range_end_match(source_text, start_match, matches[1:])
            if end_match:
                end_value = _format_time_match(end_match, fallback_period=start_match.group("period"))
                if end_value is None:
                    return ExtractedTime(start_value=start_value, text=start_match.group(0))

                return ExtractedTime(
                    start_value=start_value,
                    end_value=end_value,
                    text=_build_time_range_text(source_text, start_match, end_match),
                )

            return ExtractedTime(start_value=start_value, text=start_match.group(0))

    for text, value in AMBIGUOUS_TIME_WORDS.items():
        if text in source_text:
            return ExtractedTime(start_value=value, text=text, is_ambiguous=True)

    return ExtractedTime()


def _format_time_match(match: re.Match[str], fallback_period: str | None = None) -> str | None:
    """시간 정규식 매치를 24시간제 HH:mm 문자열로 변환합니다."""
    period = match.group("period") or fallback_period
    hour = int(match.group("hour"))
    minute = 30 if match.group("half") else int(match.group("minute") or 0)
    normalized_hour = _normalize_hour(hour, period)

    if normalized_hour is None or minute > 59:
        return None

    return f"{normalized_hour:02d}:{minute:02d}"


def _find_range_end_match(
    source_text: str,
    start_match: re.Match[str],
    candidates: list[re.Match[str]],
) -> re.Match[str] | None:
    """첫 시간 뒤에 범위 연결어가 있을 때 종료 시간 후보를 찾습니다."""
    for candidate in candidates:
        between = source_text[start_match.end():candidate.start()]
        after = source_text[candidate.end():candidate.end() + 2]
        if _is_time_range_connector(between, after):
            return candidate

    return None


def _build_time_range_text(
    source_text: str,
    start_match: re.Match[str],
    end_match: re.Match[str],
) -> str:
    """임베딩 토큰에서 제거할 전체 시간 범위 표현을 반환합니다."""
    end_index = end_match.end()
    if source_text[end_index:end_index + 2] == "까지":
        end_index += 2

    return source_text[start_match.start():end_index]


def _is_time_range_connector(between: str, after: str) -> bool:
    """두 시간 표현 사이의 텍스트가 범위 표현인지 판단합니다."""
    normalized = re.sub(r"\s+", "", between)
    if normalized in ("부터", "~", "-", "부터~", "부터-"):
        return True

    return after.startswith("까지") and between.strip() == ""


def _extract_place(source_text: str, removable_texts: list[str | None]) -> ExtractedValue:
    """날짜/시간 표현을 먼저 제거한 뒤 장소 후보를 추출합니다."""
    searchable_text = source_text
    for removable_text in removable_texts:
        if removable_text:
            searchable_text = searchable_text.replace(removable_text, " ")

    match = PLACE_PATTERN.search(searchable_text)
    if not match:
        return ExtractedValue(value=None)

    return ExtractedValue(value=match.group("place"), text=match.group(0))


def _normalize_hour(hour: int, period: str | None) -> int | None:
    """오전/오후/저녁 같은 시간대 표현을 반영해 24시간제 시각으로 보정합니다."""
    if hour < 0 or hour > 24:
        return None

    if period in ("오전", "아침", "새벽"):
        return 0 if hour == 12 else hour

    if period in ("오후", "저녁", "밤", "낮"):
        return hour if hour == 12 else hour + 12 if hour < 12 else hour

    if period == "점심":
        return hour if hour == 12 else hour + 12 if hour < 12 else hour

    if hour == 24:
        return 0

    # MVP 정책 예시에 맞춰 단독 "3시"는 15:00으로 처리합니다.
    if 1 <= hour <= 7:
        return hour + 12

    return hour


def _build_to_embedding(source_text: str, removable_texts: list[str | None]) -> list[str]:
    """원문에서 날짜/시간/장소 표현을 제거하고 추천 임베딩에 사용할 토큰 배열을 만듭니다."""
    result = source_text
    for removable_text in _dedupe_longest_first(removable_texts):
        result = result.replace(removable_text, " ")

    result = re.sub(r"\b에\b", " ", result)
    result = _normalize_spaces(result).strip(" ,.;")

    return _extract_embedding_tokens(result)


def _extract_embedding_tokens(text: str) -> list[str]:
    """Kiwi 형태소 분석으로 추천에 필요한 핵심 토큰만 추출합니다."""
    if not text:
        return []

    if KIWI is None:
        return text.split()

    tokens: list[str] = []
    for token in KIWI.tokenize(text):
        form = token.form.strip()
        tag = token.tag
        if not form or form in EMBEDDING_STOP_WORDS:
            continue

        if tag.startswith(EMBEDDING_POS_PREFIXES) or tag in EMBEDDING_POS_TAGS:
            tokens.append(form)

    return tokens if tokens else text.split()


def _next_weekday(base_date: date, weekday: int) -> date:
    """기준일 이후 가장 가까운 해당 요일 날짜를 반환합니다."""
    days_until = (weekday - base_date.weekday()) % 7
    return base_date + timedelta(days=days_until)


def _this_weekday(base_date: date, weekday: int) -> date:
    """기준일이 포함된 주의 해당 요일 날짜를 반환합니다."""
    return base_date - timedelta(days=base_date.weekday()) + timedelta(days=weekday)


def _normalize_spaces(text: str) -> str:
    """연속 공백을 하나로 줄여 정규식 매칭과 토큰 생성을 안정화합니다."""
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_longest_first(texts: list[str | None]) -> tuple[str, ...]:
    """제거 대상 문자열을 중복 제거하고 긴 표현부터 정렬해 부분 제거 오류를 방지합니다."""
    unique_texts = dict.fromkeys(text for text in texts if text)
    return tuple(sorted(unique_texts, key=len, reverse=True))

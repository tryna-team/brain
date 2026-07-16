import re
from dataclasses import dataclass
from datetime import date, timedelta


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
    re.compile(r"(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:에)?"),
    re.compile(r"(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일(?:에)?"),
    re.compile(r"(?P<year>\d{4})[-/.](?P<month>\d{1,2})[-/.](?P<day>\d{1,2})"),
    re.compile(r"(?<![\d/.-])(?P<month>\d{1,2})/(?P<day>\d{1,2})(?![\d/.-])"),
]

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
    r"(?:^|\s)(?P<place>"
    r"[가-힣A-Za-z0-9]+역\s+\d+번\s+출구"
    r"|(?:서울|부산|수원|대구|대전|광주|인천|제주|강남|홍대|신촌|건대|잠실|판교)\s+(?:[가-힣A-Za-z0-9]+(?:역|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)"
    r"|(?:[가-힣A-Za-z0-9]+(?:역|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)|시청|학교|회의실|카페|병원|공항|터미널|도서관|식당|회사|집|센터|광장|공원|대학교|대학)"
    r"|[가-힣A-Za-z0-9]+(?:시|군|구|동|읍|면|리)"
    r"|부산|서울|수원|대구|대전|광주|인천|제주"
    r")(?:에서|에)"
)


@dataclass(frozen=True)
class ParsedEvent:
    source_text: str
    date_candidate: str | None
    time_candidate: str | None
    place_candidate: str | None
    to_embedding: list[str]
    is_past_date: bool
    is_time_ambiguous: bool


@dataclass(frozen=True)
class ExtractedValue:
    value: str | None
    text: str | None = None
    removable_texts: tuple[str, ...] = ()
    is_past: bool = False
    is_ambiguous: bool = False


def parse_event_text(source_text: str) -> ParsedEvent:
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
        date_candidate=extracted_date.value,
        time_candidate=extracted_time.value,
        place_candidate=extracted_place.value,
        to_embedding=to_embedding,
        is_past_date=extracted_date.is_past,
        is_time_ambiguous=extracted_time.is_ambiguous,
    )


def _extract_date(source_text: str) -> ExtractedValue:
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

        for this_week_text in (f"이번 주 {weekday_text}", f"이번주 {weekday_text}"):
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

        for next_week_text in (f"다음 주 {weekday_text}", f"다음주 {weekday_text}"):
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


def _extract_time(source_text: str) -> ExtractedValue:
    match = TIME_PATTERN.search(source_text)
    if match:
        period = match.group("period")
        hour = int(match.group("hour"))
        minute = 30 if match.group("half") else int(match.group("minute") or 0)
        normalized_hour = _normalize_hour(hour, period)

        if normalized_hour is None or minute > 59:
            return ExtractedValue(value=None)

        return ExtractedValue(
            value=f"{normalized_hour:02d}:{minute:02d}",
            text=match.group(0),
        )

    for text, value in AMBIGUOUS_TIME_WORDS.items():
        if text in source_text:
            return ExtractedValue(value=value, text=text, is_ambiguous=True)

    return ExtractedValue(value=None)


def _extract_place(source_text: str, removable_texts: list[str | None]) -> ExtractedValue:
    searchable_text = source_text
    for removable_text in removable_texts:
        if removable_text:
            searchable_text = searchable_text.replace(removable_text, " ")

    match = PLACE_PATTERN.search(searchable_text)
    if not match:
        return ExtractedValue(value=None)

    return ExtractedValue(value=match.group("place"), text=match.group(0))


def _normalize_hour(hour: int, period: str | None) -> int | None:
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

    # MVP rule: a bare "3시" follows the policy example and is treated as 15:00.
    if 1 <= hour <= 7:
        return hour + 12

    return hour


def _build_to_embedding(source_text: str, removable_texts: list[str | None]) -> list[str]:
    result = source_text
    for removable_text in _dedupe_longest_first(removable_texts):
        result = result.replace(removable_text, " ")

    result = re.sub(r"\b에\b", " ", result)
    result = _normalize_spaces(result).strip(" ,.;")

    return result.split() if result else []


def _next_weekday(base_date: date, weekday: int) -> date:
    days_until = (weekday - base_date.weekday()) % 7
    return base_date + timedelta(days=days_until)


def _this_weekday(base_date: date, weekday: int) -> date:
    return base_date - timedelta(days=base_date.weekday()) + timedelta(days=weekday)


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_longest_first(texts: list[str | None]) -> tuple[str, ...]:
    unique_texts = dict.fromkeys(text for text in texts if text)
    return tuple(sorted(unique_texts, key=len, reverse=True))

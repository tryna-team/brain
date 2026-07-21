from datetime import date

from app.services.parser_service import parse_event_text



def test_relative_dates_use_service_timezone_today(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 22),
    )

    today_result = parser_service.parse_event_text("오늘 팀플 회의")
    tomorrow_result = parser_service.parse_event_text("내일 팀플 회의")

    assert today_result.start_date == "2026-07-22"
    assert tomorrow_result.start_date == "2026-07-23"

def test_month_day_slash_pattern_does_not_match_embedded_numeric_date():
    result = parse_event_text("2012/13/20 부산 전시회")

    assert result.start_date is None


def test_approximate_time_suffix_with_space_is_removed_from_embedding_text():
    result = parse_event_text("오후 3시 쯤 팀플 회의")

    assert result.start_time == "15:00"
    assert result.to_embedding == ["팀플", "회의"]


def test_place_parser_does_not_absorb_title_before_station_location():
    result = parse_event_text("팀플 회의 강남역에서")

    assert result.place_candidate == "강남역"
    assert result.to_embedding == ["팀플", "회의"]


def test_place_parser_does_not_absorb_title_before_multi_token_location():
    result = parse_event_text("팀플 회의 서울 시청에서")

    assert result.place_candidate == "서울 시청"
    assert result.to_embedding == ["팀플", "회의"]


def test_overlapping_relative_weekday_removals_use_longest_phrase_first():
    result = parse_event_text("다다음 월요일 팀플 회의")

    assert result.start_date is not None
    assert result.to_embedding == ["팀플", "회의"]


def test_to_embedding_returns_empty_list_for_metadata_only_input():
    result = parse_event_text("오늘 오후 3시 강남역에서")

    assert result.start_date is not None
    assert result.start_time == "15:00"
    assert result.place_candidate == "강남역"
    assert result.to_embedding == []


def test_time_range_from_to_sets_start_and_end_time():
    result = parse_event_text("금요일 3시부터 4시까지 팀플 회의")

    assert result.start_time == "15:00"
    assert result.end_time == "16:00"
    assert result.to_embedding == ["팀플", "회의"]


def test_time_range_with_tilde_sets_start_and_end_time():
    result = parse_event_text("금요일 오후 3시 ~ 4시 팀플 회의")

    assert result.start_time == "15:00"
    assert result.end_time == "16:00"
    assert result.to_embedding == ["팀플", "회의"]


def test_time_range_with_hyphen_sets_start_and_end_time():
    result = parse_event_text("금요일 오전 3시-4시 팀플 회의")

    assert result.start_time == "03:00"
    assert result.end_time == "04:00"
    assert result.to_embedding == ["팀플", "회의"]


def test_invalid_explicit_time_falls_back_to_ambiguous_period():
    result = parse_event_text("오후 25시 팀플 회의")

    assert result.start_time == "afternoon"
    assert result.end_time is None
    assert result.is_time_ambiguous is True


def test_until_suffix_without_clean_connector_is_not_time_range():
    result = parse_event_text("금요일 3시 회의 4시까지 팀플")

    assert result.start_time == "15:00"
    assert result.end_time is None
    assert result.to_embedding == ["회의", "4", "시", "팀플"]


def test_week_aliases_are_parsed_as_this_and_next_week():
    this_week = parse_event_text("요번주 금요일 팀플 회의")
    spaced_this_week = parse_event_text("요번 주 금요일 팀플 회의")
    next_week = parse_event_text("담주 금요일 팀플 회의")
    spaced_next_week = parse_event_text("담 주 금요일 팀플 회의")
    canonical_this_week = parse_event_text("이번주 금요일 팀플 회의")
    canonical_next_week = parse_event_text("다음주 금요일 팀플 회의")

    assert this_week.start_date == canonical_this_week.start_date
    assert spaced_this_week.start_date == canonical_this_week.start_date
    assert next_week.start_date == canonical_next_week.start_date
    assert spaced_next_week.start_date == canonical_next_week.start_date
    assert this_week.to_embedding == ["팀플", "회의"]
    assert next_week.to_embedding == ["팀플", "회의"]


class FakeKiwiToken:
    def __init__(self, form: str, tag: str):
        self.form = form
        self.tag = tag


class FakeKiwi:
    def tokenize(self, text: str):
        return [
            FakeKiwiToken("팀플", "NNG"),
            FakeKiwiToken("에서", "JKB"),
            FakeKiwiToken("회의", "NNG"),
            FakeKiwiToken("하다", "VV"),
        ]


def test_to_embedding_uses_kiwi_core_tokens_when_available(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(parser_service, "KIWI", FakeKiwi())

    result = parser_service.parse_event_text("금요일 3시 팀플에서 회의하다")

    assert result.to_embedding == ["팀플", "회의"]


def test_to_embedding_falls_back_to_space_tokens_without_kiwi(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(parser_service, "KIWI", None)

    result = parser_service.parse_event_text("금요일 3시 팀플 회의")

    assert result.to_embedding == ["팀플", "회의"]

from datetime import date, datetime, timezone

from app.services.parser_service import parse_event_text




def test_today_helper_uses_asia_seoul_date_boundary(monkeypatch):
    import app.services.parser_service as parser_service

    class FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            utc_time = datetime(2026, 7, 21, 15, 30, tzinfo=timezone.utc)
            return utc_time.astimezone(tz)

    monkeypatch.setattr(parser_service, "datetime", FixedDateTime)

    assert parser_service._today_in_service_timezone() == date(2026, 7, 22)

def test_relative_dates_use_service_timezone_today(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 22),
    )

    today_result = parser_service.parse_event_text("오늘 팀플 회의")
    tomorrow_result = parser_service.parse_event_text("내일 팀플 회의")
    day_after_tomorrow_result = parser_service.parse_event_text("모레 팀플 회의")
    three_days_later_result = parser_service.parse_event_text("글피 팀플 회의")

    assert today_result.start_date == "2026-07-22"
    assert today_result.date_source == "RELATIVE_EXPRESSION"
    assert tomorrow_result.start_date == "2026-07-23"
    assert tomorrow_result.date_source == "RELATIVE_EXPRESSION"
    assert day_after_tomorrow_result.start_date == "2026-07-24"
    assert day_after_tomorrow_result.date_source == "RELATIVE_EXPRESSION"
    assert day_after_tomorrow_result.to_embedding == ["팀플", "회의"]
    assert three_days_later_result.start_date == "2026-07-25"
    assert three_days_later_result.date_source == "RELATIVE_EXPRESSION"
    assert three_days_later_result.to_embedding == ["팀플", "회의"]


def test_explicit_date_source_is_marked_for_absolute_date():
    result = parse_event_text("2026년 8월 22일 부산 전시회")

    assert result.start_date == "2026-08-22"
    assert result.date_source == "EXPLICIT"

def test_explicit_date_range_sets_start_and_end_date():
    result = parse_event_text("8월 22일부터 8월 24일까지 부산 여행")

    assert result.start_date == "2026-08-22"
    assert result.end_date == "2026-08-24"
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_date_range_inherits_start_month_when_end_month_is_omitted():
    result = parse_event_text(
        "8월 20일부터 22일까지 부산 여행",
        reference_date=date(2026, 8, 17),
    )

    assert result.start_date == "2026-08-20"
    assert result.end_date == "2026-08-22"
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_date_range_allows_omitted_until_particle_after_from_particle():
    result = parse_event_text(
        "8월 21일부터 22일 부산 여행",
        reference_date=date(2026, 8, 20),
    )

    assert result.start_date == "2026-08-21"
    assert result.end_date == "2026-08-22"
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_date_range_uses_reference_month_when_until_particle_is_omitted():
    result = parse_event_text(
        "21일부터 22일 부산 여행",
        reference_date=date(2026, 8, 20),
    )

    assert result.start_date == "2026-08-21"
    assert result.end_date == "2026-08-22"
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_date_range_uses_reference_month_when_both_months_are_omitted():
    result = parse_event_text(
        "20일 부터 22일까지 부산 여행",
        reference_date=date(2026, 8, 17),
    )

    assert result.start_date == "2026-08-20"
    assert result.end_date == "2026-08-22"
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_inherited_month_date_range_does_not_roll_inverted_end_to_next_month():
    result = parse_event_text(
        "8월 30일부터 2일까지 부산 여행",
        reference_date=date(2026, 8, 17),
    )

    assert result.start_date == "2026-08-30"
    assert result.end_date is None
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_date_range_selects_earliest_standard_range_before_inherited_range():
    result = parse_event_text(
        "8월 18일부터 8월 19일까지 출장 후 8월 20일부터 22일까지 여행",
        reference_date=date(2026, 8, 17),
    )

    assert result.start_date == "2026-08-18"
    assert result.end_date == "2026-08-19"


def test_date_range_selects_earliest_inherited_range_before_standard_range():
    result = parse_event_text(
        "8월 20일부터 22일까지 여행 후 8월 24일부터 8월 25일까지 출장",
        reference_date=date(2026, 8, 17),
    )

    assert result.start_date == "2026-08-20"
    assert result.end_date == "2026-08-22"


def test_relative_date_range_sets_start_and_end_date(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 22),
    )

    result = parser_service.parse_event_text("내일부터 모레까지 워크숍")

    assert result.start_date == "2026-07-23"
    assert result.end_date == "2026-07-24"
    assert result.date_source == "RELATIVE_EXPRESSION"
    assert result.to_embedding == ["워크숍"]


def test_weekday_date_range_sets_start_and_end_date(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 22),
    )

    result = parser_service.parse_event_text("금요일부터 일요일까지 MT")

    assert result.start_date == "2026-07-24"
    assert result.end_date == "2026-07-26"
    assert result.date_source == "RELATIVE_EXPRESSION"
    assert result.to_embedding == ["MT"]

def test_weekday_date_range_rolls_end_forward_when_start_moves_to_next_week(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 8, 11),
    )

    result = parser_service.parse_event_text("월요일부터 금요일까지 제주도 여행")

    assert result.start_date == "2026-08-17"
    assert result.end_date == "2026-08-21"
    assert result.date_source == "RELATIVE_EXPRESSION"
    assert result.to_embedding == ["제주도", "여행"]


def test_qualified_this_week_end_does_not_roll_to_next_week(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 8, 11),
    )

    result = parser_service.parse_event_text("월요일부터 이번주 금요일까지 제주도 여행")

    assert result.start_date == "2026-08-10"
    assert result.end_date == "2026-08-14"
    assert result.date_source == "RELATIVE_EXPRESSION"
    assert result.to_embedding == ["제주도", "여행"]

def test_dates_without_range_connector_do_not_set_end_date():
    result = parse_event_text("8월 22일 8월 24일 부산 여행")

    assert result.start_date == "2026-08-22"
    assert result.end_date is None
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]


def test_comma_separated_dates_are_not_parsed_as_a_range():
    result = parse_event_text("8월 21일, 22일 부산 여행", reference_date=date(2026, 8, 20))

    assert result.start_date == "2026-08-21"
    assert result.end_date is None


def test_mixed_explicit_and_weekday_range_uses_relative_date_source(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 22),
    )

    result = parser_service.parse_event_text("7월 23일부터 금요일까지 워크숍")

    assert result.start_date == "2026-07-23"
    assert result.end_date == "2026-07-24"
    assert result.date_source == "RELATIVE_EXPRESSION"
    assert result.to_embedding == ["워크숍"]


def test_inverted_date_range_falls_back_to_first_date():
    result = parse_event_text("8월 24일부터 8월 22일까지 부산 여행")

    assert result.start_date == "2026-08-24"
    assert result.end_date is None
    assert result.date_source == "EXPLICIT"
    assert result.to_embedding == ["부산", "여행"]

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


def test_time_range_end_without_period_inherits_inferred_afternoon():
    result = parse_event_text("3시부터 8시까지 봉사 준비")

    assert result.start_time == "15:00"
    assert result.end_time == "20:00"
    assert result.to_embedding == ["봉사", "준비"]


def test_explicit_morning_time_range_keeps_end_morning():
    result = parse_event_text("오전 3시부터 8시까지 봉사 준비")

    assert result.start_time == "03:00"
    assert result.end_time == "08:00"
    assert result.to_embedding == ["봉사", "준비"]


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
    assert this_week.date_source == "RELATIVE_EXPRESSION"
    assert next_week.to_embedding == ["팀플", "회의"]
    assert next_week.date_source == "RELATIVE_EXPRESSION"


def test_relative_week_without_weekday_uses_current_weekday(monkeypatch):
    import app.services.parser_service as parser_service

    monkeypatch.setattr(
        parser_service,
        "_today_in_service_timezone",
        lambda: date(2026, 7, 21),
    )

    this_week = parser_service.parse_event_text("이번주 회의")
    this_week_alias = parser_service.parse_event_text("요번주 회의")
    next_week = parser_service.parse_event_text("다음주 회의")
    next_week_alias = parser_service.parse_event_text("담 주 회의")
    week_after_next = parser_service.parse_event_text("다다음주 회의")
    explicit_weekday = parser_service.parse_event_text("다음주 금요일 회의")
    weekend = parser_service.parse_event_text("다음주말 회의")

    assert this_week.start_date == "2026-07-21"
    assert this_week_alias.start_date == "2026-07-21"
    assert next_week.start_date == "2026-07-28"
    assert next_week_alias.start_date == "2026-07-28"
    assert week_after_next.start_date == "2026-08-04"
    assert explicit_weekday.start_date == "2026-07-31"
    assert weekend.start_date is None
    assert next_week.date_source == "RELATIVE_EXPRESSION"
    assert next_week.to_embedding == ["회의"]
    assert explicit_weekday.date_source == "RELATIVE_EXPRESSION"
    assert explicit_weekday.to_embedding == ["회의"]


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

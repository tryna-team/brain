from app.services.parser_service import parse_event_text


def test_month_day_slash_pattern_does_not_match_embedded_numeric_date():
    result = parse_event_text("2012/13/20 부산 전시회")

    assert result.date_candidate is None


def test_approximate_time_suffix_with_space_is_removed_from_embedding_text():
    result = parse_event_text("오후 3시 쯤 팀플 회의")

    assert result.time_candidate == "15:00"
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

    assert result.date_candidate is not None
    assert result.to_embedding == ["팀플", "회의"]

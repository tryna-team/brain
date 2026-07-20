from app.services.parser_service import parse_event_text


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

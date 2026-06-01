import datetime

from my_agent import extract_facts, normalize_date


def test_normalize_date_d_format():
    today = datetime.date(2026, 5, 31)
    assert normalize_date("발표 준비 D-3", today=today) == 3


def test_normalize_date_iso_format():
    today = datetime.date(2026, 5, 31)
    assert normalize_date("마감 2026-06-02", today=today) == 2


def test_normalize_date_month_day_format():
    today = datetime.date(2026, 5, 31)
    assert normalize_date("제출일 06/01", today=today) == 1


def test_extract_facts_returns_dict_list_schema():
    text = """AI 보고서 제출 D-2\n통계 과제 제출 2026-06-03"""
    facts = extract_facts(text)

    assert isinstance(facts, list)
    assert len(facts) == 2
    for item in facts:
        assert isinstance(item, dict)
        assert set(["task", "dday", "type", "effort", "owner", "note"]).issubset(item.keys())


def test_extract_facts_parses_iso_dday():
    text = """프랑스어 과제 제출 2026-06-02"""
    facts = extract_facts(text)
    assert len(facts) == 1
    # 테스트 실행일(today)에 따라 달라질 수 있으므로 int 타입만 검증
    assert isinstance(facts[0]["dday"], int)

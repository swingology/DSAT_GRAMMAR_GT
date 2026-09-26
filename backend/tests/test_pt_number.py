from app.models.db import Question, derive_pt_number


def test_derive_pt_number():
    assert derive_pt_number("4", None) == 4
    assert derive_pt_number("04", "") == 4
    assert derive_pt_number("10", "Test10_ENG_Sec01_Mod02B") == 10
    # Non-numeric exam codes fall back to the test name.
    assert derive_pt_number("verbal", "05") == 5
    assert derive_pt_number("SAT", "Test02_ENG_Sec01_Mod02") == 2
    assert derive_pt_number(None, "Bluebook Practice Test 5") == 5
    # Not a practice test.
    assert derive_pt_number("2026_Official_Bank", "2026_Official_Bank") is None
    assert derive_pt_number(None, None) is None
    assert derive_pt_number("", "CrackAP") is None


def test_insert_listener_sets_pt_number():
    from app.models.db import _set_pt_number_on_insert

    q = Question(source_exam_code="", source_test_name="Bluebook Practice Test 7")
    _set_pt_number_on_insert(None, None, q)
    assert q.source_pt_number == 7

    explicit = Question(source_exam_code="4", source_pt_number=9)
    _set_pt_number_on_insert(None, None, explicit)
    assert explicit.source_pt_number == 9

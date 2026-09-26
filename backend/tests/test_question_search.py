from app.routers.admin import _parse_question_search as parse


def test_question_search_classification():
    uuid = "5057eab4-9bb2-4bcd-94d9-16054f452c9a"
    assert parse(uuid) == {"kind": "id", "value": uuid}
    assert parse(" 5057EAB4 ") == {"kind": "id_prefix", "value": "5057eab4"}
    assert parse("5057eab4-9bb2")["kind"] == "id_prefix"
    assert parse("2025 PT5 M2 Q12") == {
        "kind": "source",
        "value": {"year": 2025, "pt": 5, "module": "02", "question_number": 12},
    }
    assert parse("2025 · PT05 · Sec01 · Mod02B · Q3")["value"] == {
        "year": 2025, "pt": 5, "section": "01", "module": "02B", "question_number": 3,
    }
    assert parse("2024 PT5 section 1 mod02b Q10")["value"] == {
        "year": 2024, "pt": 5, "section": "01", "module": "02B", "question_number": 10,
    }
    assert parse("practice test 5 module 2 question 4")["value"] == {
        "pt": 5, "module": "02", "question_number": 4,
    }
    assert parse("pt5")["value"] == {"pt": 5}
    assert parse("2025")["value"] == {"year": 2025}
    # Hex-only words with no digit stay text; prose that merely contains tokens stays text.
    assert parse("face")["kind"] == "text"
    assert parse("semicolon")["kind"] == "text"
    assert parse("item2 is wrong")["kind"] == "text"
    assert parse("PT5 PT6")["kind"] == "text"

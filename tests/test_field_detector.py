from automation.field_detector import detect_fields


def test_detect_fields_matches_synonyms() -> None:
    labels = ["First Name", "E-mail Address", "Upload CV"]
    found = detect_fields(labels)
    assert "first_name" in found
    assert "email" in found
    assert "resume" in found

def test_get_sections_empty(ctx):
    from trail_guide_content_server.db import get_sections
    assert get_sections() == []


def test_section_not_found(ctx):
    from trail_guide_content_server.db import get_section, delete_section
    assert get_section("does-not-exist") is None

    delete_section("does-not-exist")


def test_set_get_delete_section(ctx):
    from trail_guide_content_server.db import get_sections, get_section, set_section, delete_section

    c = set_section("test", {"title": "test", "color": "FF0000", "rank": 0})
    assert c == {"id": "test", "title": "test", "color": "FF0000", "rank": 0}

    c2 = set_section("test", {"title": "test 2", "color": "00FF00", "rank": 1})
    assert c != c2
    assert get_section("test") == {"id": "test", "title": "test 2", "color": "00FF00", "rank": 1}
    assert get_sections() == [{"id": "test", "title": "test 2", "color": "00FF00", "rank": 1}]

    delete_section("test")
    assert get_section("test") is None
    assert get_sections() == []

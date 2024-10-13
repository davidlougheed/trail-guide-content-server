def test_get_sections_empty(ctx):
    from trail_guide_content_server.db import get_sections
    assert get_sections() == []


def test_section_not_found(ctx):
    from trail_guide_content_server.db import get_section, delete_section
    assert get_section("does-not-exist") is None

    delete_section("does-not-exist")

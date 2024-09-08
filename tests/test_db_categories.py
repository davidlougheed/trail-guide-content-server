def test_get_categories_empty(ctx):
    from trail_guide_content_server.db import get_categories
    assert get_categories() == []


def test_category_not_found(ctx):
    from trail_guide_content_server.db import get_category, delete_category
    assert get_category("does-not-exist") is None

    delete_category("does-not-exist")


def test_set_get_delete_category(ctx):
    from trail_guide_content_server.db import get_categories, get_category, set_category, delete_category

    c = set_category("test", {"icon_svg": "some data"})
    assert c == {"id": "test", "icon_svg": "some data"}

    c2 = set_category("test", {"icon_svg": "some data 2"})
    assert c != c2
    assert get_category("test") == {"id": "test", "icon_svg": "some data 2"}
    assert get_categories() == [{"id": "test", "icon_svg": "some data 2"}]

    delete_category("test")
    assert get_category("test") is None
    assert get_categories() == []

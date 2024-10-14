from flask.testing import FlaskClient


def assert_404_category_detail(res):
    assert res.status_code == 404
    assert res.json == {"message": "Could not find category with ID test"}


def test_get_categories_none(client: FlaskClient):
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    assert res.json == []


def test_get_category_detail_none(client: FlaskClient):
    res = client.get("/api/v1/categories/test")
    assert_404_category_detail(res)


def mk_category():
    from trail_guide_content_server.db import set_category
    set_category("test", {"icon_svg": "some SVG path"})


def assert_test_category_detail(res):
    assert res.status_code == 200
    assert res.json == {"id": "test", "icon_svg": "some SVG path"}


def test_get_categories(client: FlaskClient):
    mk_category()

    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    assert res.json == [{"id": "test", "icon_svg": "some SVG path"}]


def test_get_category_detail(client: FlaskClient):
    mk_category()
    assert_test_category_detail(client.get("/api/v1/categories/test"))


def test_put_category_new(client: FlaskClient):
    res = client.put("/api/v1/categories/test", json={"icon_svg": "some SVG path"})
    assert res.status_code == 201
    assert_test_category_detail(client.get("/api/v1/categories/test"))


def test_put_category_new_invalid(client: FlaskClient):
    res = client.put("/api/v1/categories/test", json=[{"icon_svg": "some SVG path"}])
    assert res.status_code == 400
    assert res.json["message"] == "Request body must be a JSON object"

    res = client.put("/api/v1/categories/test", json={"icon_svggggg": "some SVG path"})
    assert res.status_code == 400
    assert res.json["message"] == "Object validation failed"


def test_delete_category(client: FlaskClient):
    mk_category()

    res = client.delete("/api/v1/categories/test")
    assert res.status_code == 200
    assert res.json == {"message": "Deleted."}

    from trail_guide_content_server.db import get_category
    assert get_category("test") is None  # make sure category was actually deleted

    assert_404_category_detail(client.get("/api/v1/categories/test"))

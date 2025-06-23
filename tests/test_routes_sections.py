import pytest
from flask.testing import FlaskClient


def test_section_empty(client: FlaskClient):
    res = client.get("/api/v1/sections")
    assert res.status_code == 200
    assert res.json == []


def test_section_404(client: FlaskClient):
    res = client.get("/api/v1/sections/does-not-exist")
    assert res.status_code == 404
    assert res.json == {"message": "Could not find section with ID does-not-exist"}


def test_section_set_get_delete(client: FlaskClient):
    test_body_1 = {"title": "test", "color": "FF0000", "rank": 0}
    test_body_2 = {"title": "test 2", "color": "00FF00", "rank": 1}

    # create a new section
    res = client.put("/api/v1/sections/test", json=test_body_1)
    assert res.status_code == 201

    # check it shows up in the list
    res = client.get("/api/v1/sections")
    assert res.json == [{"id": "test", **test_body_1}]

    # check we can access it via ID
    res = client.get("/api/v1/sections/test")
    assert res.json == {"id": "test", **test_body_1}

    # check we can update the section with new values
    res = client.put("/api/v1/sections/test", json=test_body_2)
    assert res.status_code == 200

    # check it updated
    res = client.get("/api/v1/sections/test")
    assert res.json == {"id": "test", **test_body_2}

    # check we can delete the section
    res = client.delete("/api/v1/sections/test")
    assert res.status_code == 200
    assert res.json == {"message": "Deleted."}

    # check the list is now empty
    res = client.get("/api/v1/sections")
    assert res.json == []

    # check we get 404 again
    res = client.get("/api/v1/sections/test")
    assert res.status_code == 404


@pytest.mark.parametrize(
    "bad_body",
    [
        ({"title": "test", "color": "#FF0000", "rank": 0},),
        ({"title": "test", "color": "FF0000#", "rank": 0},),
        ({"title": "test", "color": "FF000", "rank": 0},),
        ({"title": "test", "color": "XYZFFF", "rank": 0},),
    ],
)
def test_section_set_bad_color(client: FlaskClient, bad_body: dict):
    res = client.put("/api/v1/sections/test", json=bad_body)
    assert res.status_code == 400

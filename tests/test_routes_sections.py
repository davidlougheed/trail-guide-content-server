from flask.testing import FlaskClient


def test_section_empty(client: FlaskClient):
    res = client.get("/api/v1/sections")
    assert res.status_code == 200
    assert res.json == []


def test_section_404(client: FlaskClient):
    res = client.get("/api/v1/sections/does-not-exist")
    assert res.status_code == 404
    assert res.json == {"message": "Could not find section with ID does-not-exist"}

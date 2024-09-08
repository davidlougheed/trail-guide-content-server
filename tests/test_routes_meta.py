from flask.testing import FlaskClient

from trail_guide_content_server import __version__


def test_info(client: FlaskClient):
    res = client.get("/api/v1/info")
    assert res.status_code == 200
    assert res.json == {"version": __version__}


def test_config(client: FlaskClient):
    res = client.get("/api/v1/config")
    assert res.status_code == 200

    # TODO: test content

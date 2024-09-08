from flask.testing import FlaskClient

from .shared_data import TEST_IMAGE


def test_get_assets_none(client: FlaskClient):
    res = client.get("/api/v1/assets")
    assert res.status_code == 200
    assert res.json == []


def test_get_asset_detail_none(client: FlaskClient):
    res = client.get("/api/v1/assets/test")
    assert res.status_code == 404
    assert res.json == {"message": "Could not find asset with ID test"}


def test_get_asset_bytes_none(client: FlaskClient):
    res = client.get("/api/v1/assets/test/bytes")
    assert res.status_code == 404
    assert res.json == {"message": "Could not find asset with ID test"}


def test_create_asset_no_file(client: FlaskClient):
    res = client.post("/api/v1/assets")
    assert res.status_code == 400
    assert res.json == {"message": "No file provided"}


def test_create_asset_valid(client: FlaskClient):
    with open(TEST_IMAGE, "rb") as fh:
        res = client.post("/api/v1/assets", content_type="multipart/form-data", data={"file": fh})

    assert res.status_code == 201  # created
    data = res.json
    assert len(data) == 7
    assert "id" in data
    assert data["asset_type"] == "image"
    assert data["file_name"].endswith("000094970005.jpg")
    assert data["file_size"] == 3634288
    assert data["sha1_checksum"] == "c93ab7d09dd99eb59a4534a567638e9e8058208b"
    assert data["times_used_by_all"] == 0
    assert data["times_used_by_enabled"] == 0

    with open(TEST_IMAGE, "rb") as fh:
        res = client.get(f"/api/v1/assets/{data['id']}/bytes")
        assert res.status_code == 200
        assert res.content_type == "image/jpeg"
        assert res.data == fh.read()

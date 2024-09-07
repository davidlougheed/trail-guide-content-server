from flask.testing import FlaskClient


def test_station_empty(client: FlaskClient):
    res = client.get("/api/v1/stations")
    assert res.status_code == 200
    assert res.json == []


def test_station_404(client: FlaskClient):
    res = client.get("/api/v1/stations/does-not-exist")
    assert res.status_code == 404
    assert res.json == {"message": "Could not find station with ID does-not-exist"}

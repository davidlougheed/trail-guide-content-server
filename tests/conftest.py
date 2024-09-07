import os
import pytest


@pytest.fixture
def client():
    os.environ["TGCS_DATABASE"] = ":memory:"
    from trail_guide_content_server.app import application
    from trail_guide_content_server.db import init_db
    with application.app_context():
        init_db()
        yield application.test_client()

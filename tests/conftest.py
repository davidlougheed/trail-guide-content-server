import os
import pytest


@pytest.fixture
def ctx():
    os.environ["TGCS_DATABASE"] = ":memory:"
    from trail_guide_content_server.app import application
    from trail_guide_content_server.db import init_db

    with application.app_context() as ctx:
        init_db()
        yield ctx


@pytest.fixture
def client(ctx):
    from trail_guide_content_server.app import application

    yield application.test_client()

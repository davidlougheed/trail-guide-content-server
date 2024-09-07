import pytest

from trail_guide_content_server.assets import detect_asset_type
from trail_guide_content_server.types import AssetType


@pytest.mark.parametrize("fn,res,form_data", [
    ("test.mp3", "audio", None),
    ("hello/world.test.m4a", "audio", None),
    ("test.m4a.jpg", "image", None),
    (".test.image.jpeg", "image", None),
    ("test.png", "image", None),
    ("test.gif", "image", None),
    ("test.pdf", "pdf", None),
    ("test.mp4", "video", None),
    ("test.mov", "video", None),
    ("test.asdf", "video", {"asset_type": "video"}),
])
def test_detect_asset_type(fn: str, res: AssetType, form_data: dict[str, str] | None):
    assert detect_asset_type(fn, form_data=form_data) == res

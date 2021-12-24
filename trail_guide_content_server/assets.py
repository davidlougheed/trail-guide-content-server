import json

from datetime import datetime
from itertools import groupby

from .db import get_asset_types

__all__ = [
    "make_asset_list",
]


def _make_asset_list_js(assets):
    assets_by_type = {
        at: {aa["id"]: f"""require("./{at}/{aa['file_name']}")""" for aa in v}
        for at, v in groupby(assets, key=lambda x: x["asset_type"])
    }

    rt = (
        f"// Generated automatically by trail-guide-content-server\n"
        f"// at {datetime.now().isoformat()}\n"
        f"export default {{\n"
    )

    for at in get_asset_types():
        at_str = json.dumps(at)
        rt += f"    {at_str}: {{\n"
        for k, v in assets_by_type.get(at, {}).items():
            rt += f"        {json.dumps(k)}: {v},\n"

        rt += "    },\n"

    rt += "};\n"

    return rt, "application/js"


def make_asset_list(assets, as_js: bool = False):
    if as_js:
        return _make_asset_list_js(assets)

    return json.dumps(assets), "application/json"

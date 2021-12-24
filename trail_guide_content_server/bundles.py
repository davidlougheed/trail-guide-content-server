import json
import os
import pathlib
import shutil
import tempfile
import uuid
import zipfile

from flask import current_app

from .assets import make_asset_list
from .db import (
    get_assets,
    get_asset_types,
    get_layers,
    get_modals,
    get_pages,
    get_sections_with_stations,
    get_settings,
)

__all__ = [
    "make_bundle_path",
    "make_release_bundle",
]


def make_bundle_path() -> pathlib.Path:
    return pathlib.Path(current_app.config["BUNDLE_DIR"]) / f"{str(uuid.uuid4())}.zip"


def make_release_bundle(final_bundle_path: pathlib.Path):
    assets_to_include = get_assets(filter_disabled=True)

    asset_js, _ = make_asset_list(assets_to_include, as_js=True)

    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)

        os.mkdir(tdp / "assets")

        asset_path = tdp / "assets" / "assets.js"
        layers_path = tdp / "layers.json"
        modals_path = tdp / "modals.json"
        pages_path = tdp / "pages.json"
        settings_path = tdp / "settings.json"
        stations_path = tdp / "stations.json"

        bundle_name = "bundle.zip"
        bundle_path = tdp / bundle_name

        with open(asset_path, "w") as afh:
            afh.write(asset_js)

        with open(layers_path, "w") as lfh:
            json.dump(get_layers(), lfh)

        with open(modals_path, "w") as mfh:
            json.dump({m["id"]: m for m in get_modals()}, mfh)

        with open(pages_path, "w") as pfh:
            json.dump({p["id"]: p for p in get_pages(enabled_only=True)}, pfh)

        with open(settings_path, "w") as sfh:
            json.dump(get_settings(), sfh)

        with open(stations_path, "w") as sfh:
            json.dump(get_sections_with_stations(enabled_only=True), sfh)

        with open(bundle_path, "wb") as zfh:
            with zipfile.ZipFile(zfh, mode="w") as zf:
                zf.write(layers_path, "layers.json")
                zf.write(modals_path, "modals.json")
                zf.write(pages_path, "pages.json")
                zf.write(stations_path, "stations.json")

                zf.write(asset_path, "assets/assets.js")

                for asset in assets_to_include:
                    zf.write(
                        pathlib.Path(current_app.config["ASSET_DIR"]) / asset["file_name"],
                        f"assets/{asset['asset_type']}/{asset['file_name']}")

        shutil.copyfile(bundle_path, final_bundle_path)

# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2025  David Lougheed
# See NOTICE for more information.

import json
import os
import pathlib
import shutil
import tempfile
import uuid
import zipfile

from flask import current_app

from . import db
from .assets import make_asset_list
from .config import public_config

__all__ = [
    "make_bundle_path",
    "make_release_bundle",
]


def make_bundle_path() -> pathlib.Path:
    """
    Generates a randomly-named ZIP file path into which a new bundle's contents can be put.
    :return: The generated file path
    """
    return pathlib.Path(current_app.config["BUNDLE_DIR"]) / f"{str(uuid.uuid4())}.zip"


def make_release_bundle(release: dict, final_bundle_path: pathlib.Path) -> int:
    """
    Creates a release bundle from release metadata and database contents.
    :param release: Release metadata
    :param final_bundle_path: The path to put the final bundle with all contents
    :return: The size of the final bundle, in bytes
    """

    assets_to_include = db.get_assets_used()
    asset_js, _ = make_asset_list(assets_to_include, as_js=True)

    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)

        os.mkdir(tdp / "assets")

        asset_path = tdp / "assets" / "assets.js"
        categories_path = tdp / "categories.json"
        config_path = tdp / "config.json"
        layers_path = tdp / "layers.json"
        metadata_path = tdp / "metadata.json"
        modals_path = tdp / "modals.json"
        pages_path = tdp / "pages.json"
        settings_path = tdp / "settings.json"
        stations_path = tdp / "stations.json"

        bundle_name = "bundle.zip"
        bundle_path = tdp / bundle_name

        with open(asset_path, "w") as afh:
            afh.write(asset_js)

        with open(categories_path, "w") as cfh:
            json.dump({c["id"]: c for c in db.get_categories()}, cfh, indent=2)

        with open(config_path, "w") as cfh:
            json.dump(public_config, cfh, indent=2)

        with open(layers_path, "w") as lfh:
            json.dump(db.get_layers(), lfh, indent=2)

        with open(metadata_path, "w") as mfh:
            json.dump(
                {
                    "release": {k: v for k, v in release.items() if not k.endswith("_dt")},
                },
                mfh,
                indent=2,
            )

        with open(modals_path, "w") as mfh:
            json.dump({m["id"]: m for m in db.modal_model.get_all()}, mfh, indent=2)

        with open(pages_path, "w") as pfh:
            json.dump(db.page_model.get_all(enabled_only=True), pfh, indent=2)

        with open(settings_path, "w") as sfh:
            json.dump(db.get_settings(), sfh, indent=2)

        with open(stations_path, "w") as sfh:
            json.dump(db.get_sections_with_stations(enabled_only=True), sfh, indent=2)

        with open(bundle_path, "wb") as zfh:
            with zipfile.ZipFile(zfh, mode="w") as zf:
                zf.write(categories_path, "categories.json")
                zf.write(config_path, "config.json")
                zf.write(layers_path, "layers.json")
                zf.write(metadata_path, "metadata.json")
                zf.write(modals_path, "modals.json")
                zf.write(pages_path, "pages.json")
                zf.write(settings_path, "settings.json")
                zf.write(stations_path, "stations.json")

                zf.write(asset_path, "assets/assets.js")

                for asset in assets_to_include:
                    zf.write(
                        pathlib.Path(current_app.config["ASSET_DIR"]) / asset["file_name"],
                        f"assets/{asset['asset_type']}/{asset['file_name']}",
                    )

        shutil.copyfile(bundle_path, final_bundle_path)

    return os.path.getsize(final_bundle_path)

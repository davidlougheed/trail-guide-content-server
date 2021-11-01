import json
import os
import pathlib
import uuid

from datetime import datetime
from flask import Blueprint, jsonify, current_app, request, Response
from itertools import groupby
from werkzeug.utils import secure_filename

from .db import (
    get_db,

    get_categories,

    get_sections,
    get_sections_with_stations,
    get_section,
    set_section,

    get_stations,
    get_station,
    set_station,
    delete_station,

    get_asset_types,
    get_assets,
    get_asset,
    set_asset,

    get_pages,
    get_page,
    set_page,

    get_modals,
    get_modal,
    set_modal,
    delete_modal,

    get_settings,
    set_settings,
)
from .object_schemas import section_validator, station_validator, asset_validator, modal_validator

__all__ = ["api_v1"]

api_v1 = Blueprint("api", __name__)

err_must_be_object = Response(json.dumps({"message": "Request body must be an object"}), status=400)
err_cannot_alter_id = Response(json.dumps({"message": "Cannot alter object ID"}), status=400)
err_no_file = Response(json.dumps({"message": "No file provided"}), status=400)


def err_validation_failed(errs):
    return current_app.response_class(json.dumps({
        "message": "Object validation failed",
        "errors": [str(e) for e in errs],
    }), status=400)


def request_changed(old_val, form_data: bool = False, field: str = "id") -> bool:
    obj_to_check = request.form if form_data else request.json
    return field in obj_to_check and obj_to_check[field] != old_val


@api_v1.route("/categories", methods=["GET"])
def categories():
    return jsonify(get_categories())


@api_v1.route("/sections", methods=["GET"])
def sections():
    nest_stations = request.args.get("nest_stations")
    return jsonify(get_sections_with_stations() if nest_stations else get_sections())


@api_v1.route("/sections/<string:section_id>", methods=["GET", "PUT"])
def sections_detail(section_id: str):
    s = get_section(section_id)

    if s is None:
        return current_app.response_class(json.dumps(
            {"message": f"Could not find section with ID {section_id}"}), status=404)

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(s["id"]):
            return err_cannot_alter_id

        s = {**s, **request.json}

        errs = list(section_validator.iter_errors(s))
        if errs:
            return err_validation_failed(errs)

        s = set_section(section_id, s)

    return jsonify(s)


@api_v1.route("/stations", methods=["GET", "POST"])
def stations():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        station_id = str(uuid.uuid4())

        s = {"id": station_id, **request.json}

        errs = list(station_validator.iter_errors(s))
        if errs:
            return err_validation_failed(errs)

        return set_station(station_id, s)

    return jsonify(get_stations())


@api_v1.route("/stations/<string:station_id>", methods=["GET", "PUT", "DELETE"])
def stations_detail(station_id: str):
    s = get_station(station_id)

    if s is None:
        return current_app.response_class(json.dumps(
            {"message": f"Could not find station with ID {station_id}"}), status=404)

    # TODO: Delete
    if request.method == "DELETE":
        delete_station(station_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(s["id"]):
            return err_cannot_alter_id

        s = {**s, **request.json}

        errs = list(section_validator.iter_errors(s))
        if errs:
            return err_validation_failed(errs)

        s = set_station(station_id, s)

    return jsonify(s)


@api_v1.route("/asset_types", methods=["GET"])
def asset_types():
    return jsonify(get_asset_types())


def _detect_asset_type(file_name: str) -> tuple[str, str]:
    file_ext = os.path.splitext(file_name)[1].lower().lstrip(".")

    # TODO: py3.10: match
    if file_ext in {"jpg", "jpeg", "png", "gif"}:
        asset_type = "image"
    elif file_ext in {"mp3", "m4a"}:
        asset_type = "audio"
    elif file_ext in {"mp4", "mov"}:
        asset_type = "video"
    elif file_ext in {"vtt"}:
        asset_type = "video_text_track"
    else:
        if "asset_type" not in request.form:
            return "", "No asset_type provided, and could not figure it out automatically"

        asset_type = request.form["asset_type"]

    return asset_type, ""


@api_v1.route("/assets", methods=["GET", "POST"])
def asset_list():
    if request.method == "POST":
        if "file" not in request.files:
            return err_no_file

        asset_id = str(uuid.uuid4())
        file = request.files["file"]

        asset_type, err = _detect_asset_type(file.filename)
        if err:
            return current_app.response_class(json.dumps({"message": err}), status=400)

        file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file.filename)}"
        file_path = pathlib.Path(current_app.config["ASSET_DIR"]) / file_name

        get_db()  # Make sure the DB can be initialized before we start doing file stuff

        file.save(file_path)

        a = {
            "id": asset_id,
            "asset_type": asset_type,
            "file_name": file_name,
            "file_size": os.path.getsize(file_path),
        }

        errs = list(asset_validator.iter_errors(a))
        if errs:
            return err_validation_failed(errs)

        return jsonify(set_asset(a["id"], a))

    as_js = request.args.get("as_js")

    assets = get_assets()
    assets_by_type = {
        at: {aa["id"]: f"""require("./{at}/{aa['file_name']}")""" for aa in v}
        for at, v in groupby(assets, key=lambda x: x["asset_type"])
    }

    if as_js:
        rt = "export default {\n"

        for at in get_asset_types():
            at_str = json.dumps(at)
            rt += f"    {at_str}: {{\n"
            for k, v in assets_by_type.get(at, {}).items():
                rt += f"        {json.dumps(k)}: {v},\n"

            rt += "    },\n"

        rt += "};\n"

        return current_app.response_class(rt, content_type="application/js")

    return jsonify(assets)


@api_v1.route("/assets/<string:asset_id>", methods=["GET", "PUT", "DELETE"])
def asset_detail(asset_id):
    a = get_asset(asset_id)

    if a is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find asset with ID {asset_id}"}), status=404)

    if request.method == "DELETE":
        # TODO: Delete object and bytes
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if request_changed(a["id"], form_data=True):
            return err_cannot_alter_id

        # Don't let users change asset_type, since the asset may already have been embedded as HTML in
        # a document somewhere - which we cannot fix the markup for.
        if request_changed(a["asset_type"], form_data=True, field="asset_type"):
            return current_app.response_class(jsonify({"message": "Cannot change asset type."}), status=400)

        a = {
            **a,
            "enabled": request.form["enabled"],
        }

        if "file" in request.files:
            # Changing file, so handle the upload

            file = request.files["file"]

            asset_type, err = _detect_asset_type(file.filename)
            if err:
                return current_app.response_class(jsonify({"message": err}), status=400)

            asset_dir = pathlib.Path(current_app.config["ASSET_DIR"])
            file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file.filename)}"
            file_path = asset_dir / file_name

            get_db()  # Make sure the DB can be initialized before we start doing file stuff

            old_file_name = a["file_name"]
            file.save(file_path)
            os.remove(asset_dir / old_file_name)

            a = {
                **a,
                "asset_type": asset_type,
                "file_name": file_name,
                "file_size": os.path.getsize(file_path),
            }

            errs = list(asset_validator.iter_errors(a))
            if errs:
                os.remove(file_path)
                return err_validation_failed(errs)

        else:
            errs = list(asset_validator.iter_errors(a))
            if errs:
                return err_validation_failed(errs)

        a = set_asset(asset_id, a)

    return jsonify(a)


@api_v1.route("/assets/<string:asset_id>/bytes", methods=["GET"])
def assets_bytes(asset_id: str):
    a = get_asset(asset_id)

    if a is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find asset with ID {asset_id}"}), status=404)

    with open(pathlib.Path(current_app.config["ASSET_DIR"] / a["file_name"]), "rb") as fh:
        r = current_app.response_class(fh.read())
        r.headers.set("Content-Type", "application/octet-stream")
        r.headers.set("Content-Disposition", f"attachment; filename={a['file_name']}")
        return r


# TODO: Create page functionality
@api_v1.route("/pages", methods=["GET"])
def pages():
    return jsonify(get_pages())


# TODO: Delete page functionality when create page is done
@api_v1.route("/pages/<string:page_id>", methods=["GET", "PUT"])
def pages_detail(page_id: str):
    p = get_page(page_id)

    if p is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find page with ID {page_id}"}), status=404)

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(p["id"]):
            return err_cannot_alter_id

        p = {**p, **request.json}

        errs = list(section_validator.iter_errors(p))
        if errs:
            return err_validation_failed(errs)

        p = set_page(page_id, p)

    return jsonify(p)


@api_v1.route("/modals", methods=["GET", "POST"])
def modals():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        # Let users set IDs for now
        m = {**request.json}

        errs = list(modal_validator.iter_errors(m))
        if errs:
            return err_validation_failed(errs)

        return set_modal(m["id"], m)

    return jsonify(get_modals())


@api_v1.route("/modals/<string:modal_id>", methods=["DELETE", "GET", "PUT"])
def modals_detail(modal_id: str):
    m = get_modal(modal_id)

    if m is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find modal with ID {modal_id}"}), status=404)

    if request.method == "DELETE":
        delete_modal(modal_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request.json.get("id") != m["id"]:
            return err_cannot_alter_id

        m = {**m, **request.json}

        errs = list(modal_validator.iter_errors(m))
        if errs:
            return err_validation_failed(errs)

        m = set_modal(modal_id, m)

    return jsonify(m)


@api_v1.route("/settings", methods=["GET", "PUT"])
def settings():
    s = get_settings()

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        s = set_settings({str(k): v for k, v in request.json.items()})

    return jsonify(s)

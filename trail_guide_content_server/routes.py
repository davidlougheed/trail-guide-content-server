# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2022  David Lougheed
# See NOTICE for more information.

import json
import os
import pathlib
import traceback
import uuid

from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, current_app, request, Response, send_file
from werkzeug.utils import secure_filename

from .assets import detect_asset_type, make_asset_list
from .auth import requires_auth, SCOPE_READ_CONTENT
from .bundles import make_bundle_path, make_release_bundle
from .config import public_config
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

    get_layers,
    get_layer,
    set_layer,
    delete_layer,

    get_releases,
    get_release,
    set_release,

    get_settings,
    set_settings,

    get_feedback_items,
    set_feedback_item,

    set_ott,
)
from .object_schemas import (
    section_validator,
    station_validator,
    asset_validator,
    modal_validator,
    layer_validator,
    release_validator,
    feedback_item_validator,
)
from .qr import make_station_qr
from .utils import get_file_hash_hex, get_utc_str, request_changed

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


@api_v1.route("/categories", methods=["GET"])
@requires_auth
def categories():
    return jsonify(get_categories())


@api_v1.route("/sections", methods=["GET"])
@requires_auth
def sections():
    nest_stations = request.args.get("nest_stations")
    return jsonify(get_sections_with_stations() if nest_stations else get_sections())


@api_v1.route("/sections/<string:section_id>", methods=["GET", "PUT"])
@requires_auth
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
@requires_auth
def stations():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        s = {"id": str(uuid.uuid4()), **request.json}

        errs = list(station_validator.iter_errors(s))
        if errs:
            return err_validation_failed(errs)

        return jsonify(set_station(s["id"], s))

    return jsonify(get_stations())


@api_v1.route("/stations/<string:station_id>", methods=["GET", "PUT", "DELETE"])
@requires_auth
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


@api_v1.route("/stations/<string:station_id>/qr", methods=["GET"])
def stations_qr(station_id: str):
    s = get_station(station_id)

    if s is None:
        return current_app.response_class(status=404)

    r = current_app.response_class(make_station_qr(station_id))
    r.headers.set("Content-Type", "image/png")
    r.headers.set("Content-Disposition", f"inline; filename=station-qr-{station_id}.png")
    return r


@api_v1.route("/asset_types", methods=["GET"])
@requires_auth
def asset_types():
    return jsonify(get_asset_types())


@api_v1.route("/assets", methods=["GET", "POST"])
@requires_auth
def asset_list():
    if request.method == "POST":
        if "file" not in request.files:
            return err_no_file

        file = request.files["file"]

        asset_type, err = detect_asset_type(file.filename, request.form)
        if err:
            return current_app.response_class(json.dumps({"message": err}), status=400)

        file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file.filename)}"
        file_path = pathlib.Path(current_app.config["ASSET_DIR"]) / file_name

        get_db()  # Make sure the DB can be initialized before we start doing file stuff

        file.save(file_path)

        a = {
            "id": str(uuid.uuid4()),
            "asset_type": asset_type,
            "file_name": file_name,
            "file_size": os.path.getsize(file_path),
            "sha1_checksum": get_file_hash_hex(file_path),
            "enabled": request.form.get("enabled", "").strip() != "",
        }

        errs = list(asset_validator.iter_errors(a))
        if errs:
            return err_validation_failed(errs)

        return jsonify(set_asset(a["id"], a))

    as_js = request.args.get("as_js", "").strip() != ""
    rt, ct = make_asset_list(get_assets(), as_js=as_js)
    return current_app.response_class(rt, content_type=ct)


@api_v1.route("/assets/<string:asset_id>", methods=["GET", "PUT", "DELETE"])
@requires_auth
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
            "enabled": request.form.get("enabled", "").strip() != "",
        }

        if "file" in request.files:
            # Changing file, so handle the upload

            file = request.files["file"]

            asset_type, err = detect_asset_type(file.filename, request.form)
            if err:
                return current_app.response_class(jsonify({"message": err}), status=400)

            asset_dir = pathlib.Path(current_app.config["ASSET_DIR"])
            file_parts = secure_filename(file.filename).split(".")
            file_name = f"{''.join(file_parts[:-1])}-{int(datetime.now().timestamp() * 1000)}.{file_parts[-1]}"
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

            if errs := list(asset_validator.iter_errors(a)):
                os.remove(file_path)
                return err_validation_failed(errs)

        else:
            if errs := list(asset_validator.iter_errors(a)):
                return err_validation_failed(errs)

        a = set_asset(asset_id, a)

    return jsonify(a)


@api_v1.route("/assets/<string:asset_id>/bytes", methods=["GET"])
def assets_bytes(asset_id: str):
    a = get_asset(asset_id)

    if a is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find asset with ID {asset_id}"}), status=404)

    content_type = "application/octet-stream"
    file_ext = os.path.splitext(a["file_name"])[1].lstrip(".").lower()

    # TODO: py3.10: match
    if a["asset_type"] == "image":
        if file_ext in {"jpg", "jpeg"}:
            content_type = "image/jpeg"
        elif file_ext == "png":
            content_type = "image/png"
        elif file_ext == "gif":
            content_type = "image/gif"
    elif a["asset_type"] == "audio":
        if file_ext == "mp3":
            content_type = "audio/mp3"
        elif file_ext == "m4a":
            content_type = "audio/m4a"
    elif a["asset_type"] == "video":
        if file_ext == "mp4":
            content_type = "video/mp4"
        elif file_ext == "mov":
            content_type = "video/quicktime"
    elif a["asset_type"] == "video_text_track":
        if file_ext == "vtt":
            content_type = "text/vvt"

    with open(pathlib.Path(current_app.config["ASSET_DIR"]) / a["file_name"], "rb") as fh:
        r = current_app.response_class(fh.read())
        r.headers.set("Content-Type", content_type)
        if content_type == "application/octet-stream":
            r.headers.set("Content-Disposition", f"attachment; filename={a['file_name']}")
        return r


# TODO: Create page functionality
@api_v1.route("/pages", methods=["GET"])
@requires_auth
def pages():
    return jsonify(get_pages())


# TODO: Delete page functionality when create page is done
@api_v1.route("/pages/<string:page_id>", methods=["GET", "PUT"])
@requires_auth
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

        if errs := list(section_validator.iter_errors(p)):
            return err_validation_failed(errs)

        p = set_page(page_id, p)

    return jsonify(p)


@api_v1.route("/modals", methods=["GET", "POST"])
@requires_auth
def modals():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        m = {"id": str(uuid.uuid4()), **request.json}

        if errs := list(modal_validator.iter_errors(m)):
            return err_validation_failed(errs)

        return jsonify(set_modal(m["id"], m))

    return jsonify(get_modals())


@api_v1.route("/modals/<string:modal_id>", methods=["DELETE", "GET", "PUT"])
@requires_auth
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

        if request_changed(m["id"]):
            return err_cannot_alter_id

        m = {**m, **request.json}

        if errs := list(modal_validator.iter_errors(m)):
            return err_validation_failed(errs)

        m = set_modal(modal_id, m)

    return jsonify(m)


@api_v1.route("/layers", methods=["GET", "POST"])
@requires_auth
def layers():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        layer = {"id": str(uuid.uuid4()), **request.json}

        errs = list(layer_validator.iter_errors(layer))
        if errs:
            return err_validation_failed(errs)

        return jsonify(set_layer(layer["id"], layer))

    return jsonify(get_layers())


@api_v1.route("/layers/<string:layer_id>", methods=["DELETE", "GET", "PUT"])
@requires_auth
def layers_detail(layer_id: str):
    layer = get_layer(layer_id)

    if layer is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find layer with ID {layer_id}"}), status=404)

    if request.method == "DELETE":
        delete_layer(layer_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(layer["id"]):
            return err_cannot_alter_id

        layer = {**layer, **request.json}

        errs = list(layer_validator.iter_errors(layer))
        if errs:
            return err_validation_failed(errs)

        layer = set_layer(layer_id, layer)

    return jsonify(layer)


@api_v1.route("/releases", methods=["GET", "POST"])
@requires_auth
def releases():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        bundle_path = make_bundle_path()

        r = {
            "version": 0,  # Dummy ID for validation
            **request.json,
            "bundle_path": str(bundle_path),
            "submitted_dt": get_utc_str(),
            "published_dt": None,
        }

        if errs := list(release_validator.iter_errors(r)):
            return err_validation_failed(errs)

        db = get_db()
        c = db.cursor()

        try:
            c.execute("BEGIN")  # Put SQLite into manual commit mode
            r = set_release(None, r, commit=False)
            make_release_bundle(r, bundle_path)
            db.commit()
        except Exception as e:
            print("Warning: encountered exception while making bundle", e)
            traceback.print_exc()
            db.rollback()
            return current_app.response_class(json.dumps({
                "message": "Error encountered while generating release",
                "errors": [traceback.format_exc()],
            }), status=500)

        return jsonify(r)

    return jsonify(get_releases())


@api_v1.route("/releases/<int:version>", methods=["GET"])
@requires_auth
def releases_detail(version: int):
    r = get_release(version)

    if r is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find version {version}"}), status=404)

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(r["version"]):
            return err_cannot_alter_id

        if request_changed(r["bundle_path"], field="bundle_path"):
            return current_app.response_class(jsonify({"message": f"Cannot alter bundle path"}), status=400)

        if request_changed(r["submitted_dt"], field="submitted_dt"):
            return current_app.response_class(jsonify({"message": f"Cannot alter submitted date/time"}), status=400)

        published_dt = request.json.get("published_dt", request.json.get("published"))
        if r["published_dt"] is None and published_dt:
            # Overwrite user-set published time
            published_dt = get_utc_str()

        r = {**r, **request.json, "published_dt": published_dt}

        if errs := list(release_validator.iter_errors(r)):
            return err_validation_failed(errs)

        r = set_release(version, r)

    return jsonify(r)


@api_v1.route("/releases/<int:version>/bundle", methods=["GET"])
@requires_auth
def releases_bundle(version: int):
    r = get_release(version)

    if r is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find version {version}"}), status=404)

    return send_file(
        r["bundle_path"], mimetype="application/zip", as_attachment=True, download_name=f"version_{r['version']}.zip")


@api_v1.route("/settings", methods=["GET", "PUT"])
@requires_auth
def settings():
    s = get_settings()

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        s = set_settings({str(k): v for k, v in request.json.items()})

    return jsonify(s)


@api_v1.route("/config", methods=["GET"])
def config():
    return jsonify(public_config)


@api_v1.route("/feedback", methods=["GET", "POST"])
@requires_auth
def feedback():
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        f = {
            "id": str(uuid.uuid4()),
            **request.json,
            "submitted": get_utc_str(),
        }

        if errs := list(feedback_item_validator.iter_errors(f)):
            return err_validation_failed(errs)

        return jsonify(set_feedback_item(f["id"], f))

    return jsonify(get_feedback_items())


@api_v1.route("/ott", methods=["POST"])
@requires_auth
def ott():
    new_token = str(uuid.uuid4())
    t = {
        "token": new_token,
        "scope": SCOPE_READ_CONTENT,  # Currently: ignore Bearer scope
        "expiry": (datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc) + timedelta(seconds=60)).isoformat()
    }
    return jsonify(set_ott(new_token, t))

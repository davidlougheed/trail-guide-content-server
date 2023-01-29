# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2023  David Lougheed
# See NOTICE for more information.

import json
import os
import pathlib
import sys
import traceback
import uuid

from datetime import datetime, timedelta, timezone
from flask import after_this_request, Blueprint, jsonify, current_app, request, Response, send_file
from werkzeug.utils import secure_filename

from . import __version__, db
from .assets import detect_asset_type, make_asset_list
from .auth import requires_auth, SCOPE_READ_CONTENT, SCOPE_READ_RELEASES, SCOPE_MANAGE_CONTENT, SCOPE_EDIT_RELEASES
from .bundles import make_bundle_path, make_release_bundle
from .config import public_config
from .object_schemas import (
    section_validator,
    station_validator,
    asset_validator,
    modal_validator,
    layer_validator,
    release_validator,
    feedback_item_validator,
)
from .qr import make_station_qr, make_page_qr
from .utils import get_file_hash_hex, get_utc_str, request_changed

__all__ = ["api_v1", "well_known"]

ResponseType = Response | dict | tuple[dict, int]

api_v1 = Blueprint("api", __name__)
well_known = Blueprint("well_known", __name__)

err_must_be_object = Response(json.dumps({"message": "Request body must be an object"}), status=400)
err_cannot_alter_id = Response(json.dumps({"message": "Cannot alter object ID"}), status=400)
err_no_file = Response(json.dumps({"message": "No file provided"}), status=400)


def err_validation_failed(errs):
    return current_app.response_class(json.dumps({
        "message": "Object validation failed",
        "errors": [str(e) for e in errs],
    }), status=400)


@api_v1.route("/info", methods=["GET"])
def service_info() -> ResponseType:
    return {
        "version": __version__,
    }


@api_v1.route("/config", methods=["GET"])
def config() -> ResponseType:
    return jsonify(public_config)


@api_v1.route("/categories", methods=["GET"])
@requires_auth()
def categories() -> ResponseType:
    return jsonify(db.get_categories())


@api_v1.route("/sections", methods=["GET"])
@requires_auth()
def sections() -> ResponseType:
    nest_stations = request.args.get("nest_stations")
    return jsonify(db.get_sections_with_stations() if nest_stations else db.get_sections())


@api_v1.route("/sections/<string:section_id>", methods=["GET", "PUT"])
@requires_auth()
def sections_detail(section_id: str) -> ResponseType:
    s = db.get_section(section_id)

    if s is None:
        return {"message": f"Could not find section with ID {section_id}"}, 404

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(s["id"]):
            return err_cannot_alter_id

        s = {**s, **request.json}

        if errs := list(section_validator.iter_errors(s)):
            return err_validation_failed(errs)

        s = db.set_section(section_id, s)

    return jsonify(s)


@api_v1.route("/stations", methods=["GET", "POST"])
@requires_auth()
def stations() -> ResponseType:
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        s = {"id": str(uuid.uuid4()), **request.json}

        if errs := list(station_validator.iter_errors(s)):
            return err_validation_failed(errs)

        return jsonify(db.station_model.set_obj(s["id"], s))

    return jsonify(db.station_model.get_all())


@api_v1.route("/stations/<string:station_id>", methods=["GET", "PUT", "DELETE"])
@requires_auth()
def stations_detail(station_id: str) -> ResponseType:
    s = db.station_model.get_one(station_id)

    if s is None:
        return {"message": f"Could not find station with ID {station_id}"}, 404

    if request.method == "DELETE":
        db.station_model.delete_obj(station_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(s["id"]):
            return err_cannot_alter_id

        s = {**s, **request.json}

        if errs := list(section_validator.iter_errors(s)):
            return err_validation_failed(errs)

        s = db.station_model.set_obj(station_id, s)

    return jsonify(s)


@api_v1.route("/stations/<string:station_id>/revision/<int:revision_id>", methods=["GET"])
@requires_auth()
def stations_revision(station_id: str, revision_id: int) -> ResponseType:
    s = db.station_model.get_one(station_id, revision=revision_id)
    if s is None:
        return {"message": f"Could not find either station {station_id} or revision {revision_id}"}, 404
    return jsonify(s)


@api_v1.route("/stations/<string:station_id>/qr", methods=["GET"])
def stations_qr(station_id: str) -> ResponseType:
    s = db.station_model.get_one(station_id)

    if s is None:
        return current_app.response_class(status=404)

    r = current_app.response_class(make_station_qr(station_id))
    r.headers.set("Content-Type", "image/png")
    r.headers.set("Content-Disposition", f"inline; filename=station-qr-{station_id}.png")
    r.cache_control.max_age = 31536000
    r.cache_control.public = True
    r.cache_control.immutable = True
    return r


@api_v1.route("/asset_types", methods=["GET"])
@requires_auth()
def asset_types() -> ResponseType:
    return jsonify(db.get_asset_types())


@api_v1.route("/assets", methods=["GET", "POST"])
@requires_auth()
def asset_list() -> ResponseType:
    if request.method == "POST":
        if "file" not in request.files:
            return err_no_file

        file = request.files["file"]

        if not file.filename:
            return {"message": "missing filename for file"}, 400

        asset_type, err = detect_asset_type(file.filename, request.form)
        if err:
            return {"message": err}, 400

        file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file.filename)}"
        file_path = pathlib.Path(current_app.config["ASSET_DIR"]) / file_name

        db.get_db()  # Make sure the DB can be initialized before we start doing file stuff

        file.save(file_path)

        a: dict = {
            "id": str(uuid.uuid4()),
            "asset_type": asset_type,
            "file_name": file_name,
            "file_size": os.path.getsize(file_path),
            "sha1_checksum": get_file_hash_hex(file_path),
            "times_used": 0,
        }

        errs = list(asset_validator.iter_errors(a))
        if errs:
            return err_validation_failed(errs)

        return jsonify(db.set_asset(a["id"], a))

    only_used = request.args.get("only_used", "").strip() != ""
    as_js = request.args.get("as_js", "").strip() != ""

    rt, ct = make_asset_list((db.get_assets_used if only_used else db.get_assets)(), as_js=as_js)
    return current_app.response_class(rt, content_type=ct)


@api_v1.route("/assets/<string:asset_id>", methods=["GET", "PUT", "DELETE"])
@requires_auth()
def asset_detail(asset_id) -> ResponseType:
    a = db.get_asset(asset_id)

    if a is None:
        return {"message": f"Could not find asset with ID {asset_id}"}, 404

    if request.method == "DELETE":
        asset_path = pathlib.Path(current_app.config["ASSET_DIR"]) / a["file_name"]
        if asset_path.exists():
            asset_path.unlink()
        db.delete_asset(asset_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if request_changed(a["id"], form_data=True):
            return err_cannot_alter_id

        # Don't let users change asset_type, since the asset may already have been embedded as HTML in
        # a document somewhere - which we cannot fix the markup for.
        if request_changed(a["asset_type"], form_data=True, field="asset_type"):
            return {"message": "Cannot change asset type."}, 400

        if "file" in request.files:
            # Changing file, so handle the upload

            file = request.files["file"]

            if not file.filename:
                return {"message": "missing filename for file"}, 400

            asset_type, err = detect_asset_type(file.filename, request.form)
            if err:
                return {"message": err}, 400

            asset_dir = pathlib.Path(current_app.config["ASSET_DIR"])
            file_parts = secure_filename(file.filename).split(".")
            file_name = f"{''.join(file_parts[:-1])}-{int(datetime.now().timestamp() * 1000)}.{file_parts[-1]}"
            file_path = asset_dir / file_name

            db.get_db()  # Make sure the DB can be initialized before we start doing file stuff

            old_file_name = a["file_name"]
            file.save(file_path)
            os.remove(asset_dir / old_file_name)

            a = {
                **a,
                "asset_type": asset_type,
                "file_name": file_name,
                "file_size": os.path.getsize(file_path),
                "sha1_checksum": get_file_hash_hex(file_path),
            }

            if errs := list(asset_validator.iter_errors(a)):
                os.remove(file_path)
                return err_validation_failed(errs)

        else:
            if errs := list(asset_validator.iter_errors(a)):
                return err_validation_failed(errs)

        a = db.set_asset(asset_id, a)

    return jsonify(a)


@api_v1.route("/assets/<string:asset_id>/usage", methods=["GET"])
@requires_auth()
def asset_usage(asset_id: str) -> ResponseType:
    return {
        "modals": db.modal_model.get_asset_usage(asset_id),
        "pages": db.page_model.get_asset_usage(asset_id),
        "stations": db.station_model.get_asset_usage(asset_id),
    }


CT_OCTET_STREAM = "application/octet-stream"


def _get_content_type(asset_type: str, file_ext: str) -> str:
    match (asset_type, file_ext):
        case ("image", "jpg" | "jpeg"):
            return "image/jpeg"
        case ("image", "png"):
            return "image/png"
        case ("image", "gif"):
            return "image/gif"

        case ("audio", "mp3"):
            return "audio/mp3"
        case ("audio", "m4a"):
            return "audio/m4a"

        case ("video", "mp4"):
            return "video/mp4"
        case ("video", "mov"):
            return "video/quicktime"

        case ("video_text_track", "vtt"):
            return "text/vvt"

        case _:
            return CT_OCTET_STREAM


@api_v1.route("/assets/<string:asset_id>/bytes", methods=["GET"])
def assets_bytes(asset_id: str) -> ResponseType:
    a = db.get_asset(asset_id)

    if a is None:
        return {"message": f"Could not find asset with ID {asset_id}"}, 404

    file_name = a["file_name"]
    file_ext = os.path.splitext(file_name)[1].lstrip(".").lower()
    content_type = _get_content_type(a["asset_type"], file_ext)

    with open(pathlib.Path(current_app.config["ASSET_DIR"]) / file_name, "rb") as fh:
        r = current_app.response_class(fh.read())
        r.headers.set("Content-Type", content_type)
        r.cache_control.max_age = 31536000
        r.cache_control.public = True
        r.cache_control.immutable = True
        if content_type == CT_OCTET_STREAM:
            r.headers.set("Content-Disposition", f"attachment; filename={file_name}")
        return r


@api_v1.route("/pages", methods=["GET"])
@requires_auth()
def pages() -> ResponseType:
    # This endpoint isn't used for page creation, since page IDs are user-generated.
    # The PUT endpoint for the detail function (below) can be used instead.
    return jsonify(db.page_model.get_all())


# TODO: Delete page functionality when create page is done
@api_v1.route("/pages/<string:page_id>", methods=["GET", "PUT"])
@requires_auth()
def pages_detail(page_id: str) -> ResponseType:
    p = db.page_model.get_one(page_id)

    match request.method:
        case "GET":
            if p is None:
                return {"message": f"Could not find page with ID {page_id}"}, 404

        case "PUT":
            if not isinstance(request.json, dict):
                return err_must_be_object

            if p and request_changed(p["id"]):
                return err_cannot_alter_id

            p = {**(p or {}), **request.json}

            if errs := list(section_validator.iter_errors(p)):
                return err_validation_failed(errs)

            p = db.page_model.set_obj(page_id, p)

    return jsonify(p)


@api_v1.route("/pages/<string:page_id>/revision/<int:revision_id>", methods=["GET"])
@requires_auth()
def pages_revision(page_id: str, revision_id: int) -> ResponseType:
    p = db.page_model.get_one(page_id, revision=revision_id)
    if p is None:
        return {"message": f"Could not find either page {page_id} or revision {revision_id}"}, 404
    return jsonify(p)


@api_v1.route("/pages/<string:page_id>/qr", methods=["GET"])
def pages_qr(page_id: str) -> ResponseType:
    p = db.page_model.get_one(page_id)

    if p is None:
        return current_app.response_class(status=404)

    r = current_app.response_class(make_page_qr(page_id))
    r.headers.set("Content-Type", "image/png")
    r.headers.set("Content-Disposition", f"inline; filename=page-qr-{page_id}.png")
    r.cache_control.max_age = 31536000
    r.cache_control.public = True
    r.cache_control.immutable = True
    return r


@api_v1.route("/modals", methods=["GET", "POST"])
@requires_auth()
def modals() -> ResponseType:
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        m = {"id": str(uuid.uuid4()), **request.json}

        if errs := list(modal_validator.iter_errors(m)):
            return err_validation_failed(errs)

        return jsonify(db.modal_model.set_obj(m["id"], m))

    return jsonify(db.modal_model.get_all())


@api_v1.route("/modals/<string:modal_id>", methods=["DELETE", "GET", "PUT"])
@requires_auth()
def modals_detail(modal_id: str) -> ResponseType:
    m = db.modal_model.get_one(modal_id)

    match request.method:
        case "GET":
            if m is None:
                return {"message": f"Could not find modal with ID {modal_id}"}, 404

        case "DELETE":
            db.modal_model.delete_obj(modal_id)
            return jsonify({"message": "Deleted."})

        case "PUT":
            if not isinstance(request.json, dict):
                return err_must_be_object

            if m and request_changed(m["id"]):
                return err_cannot_alter_id

            m = {**(m or {}), **request.json}

            if errs := list(modal_validator.iter_errors(m)):
                return err_validation_failed(errs)

            m = db.modal_model.set_obj(modal_id, m)

    return jsonify(m)


@api_v1.route("/modals/<string:modal_id>/revision/<int:revision_id>", methods=["GET"])
@requires_auth()
def modals_revision(modal_id: str, revision_id: int) -> ResponseType:
    m = db.modal_model.get_one(modal_id, revision=revision_id)
    if m is None:
        return {"message": f"Could not find either modal {modal_id} or revision {revision_id}"}, 404
    return jsonify(m)


@api_v1.route("/layers", methods=["GET", "POST"])
@requires_auth()
def layers() -> ResponseType:
    if request.method == "POST":
        if not isinstance(request.json, dict):
            return err_must_be_object

        layer = {"id": str(uuid.uuid4()), **request.json}

        if errs := list(layer_validator.iter_errors(layer)):
            return err_validation_failed(errs)

        return jsonify(db.set_layer(layer["id"], layer))

    return jsonify(db.get_layers())


@api_v1.route("/layers/<string:layer_id>", methods=["DELETE", "GET", "PUT"])
@requires_auth()
def layers_detail(layer_id: str) -> ResponseType:
    layer: dict | None = db.get_layer(layer_id)

    match request.method:
        case "GET":
            if layer is None:  # doesn't exist, or deleted
                return {"message": f"Could not find layer with ID {layer_id}"}, 404

        case "DELETE":
            db.delete_layer(layer_id)
            return jsonify({"message": "Deleted."})

        case "PUT":
            if not isinstance(request.json, dict):
                return err_must_be_object

            if layer and request_changed(layer["id"]):
                return err_cannot_alter_id

            layer = {**(layer or {}), **request.json}

            errs = list(layer_validator.iter_errors(layer))
            if errs:
                return err_validation_failed(errs)

            layer = db.set_layer(layer_id, layer)

    return jsonify(layer)


@api_v1.route("/ad-hoc-bundle", methods=["GET"])
@requires_auth(read_scopes=(SCOPE_READ_CONTENT, SCOPE_READ_RELEASES))
def ad_hoc_bundle() -> ResponseType:
    rel = db.get_latest_release()

    if rel is None:  # no release yet
        # TODO: more elegant way to do this - without needing at least 1 release first...
        return {"message": "no release to base ad-hoc bundle off of"}, 404

    bundle_path = make_bundle_path()
    make_release_bundle(rel, bundle_path)

    @after_this_request
    def remove_file(res):
        bundle_path.unlink(missing_ok=True)
        return res

    return send_file(bundle_path, mimetype="application/zip", as_attachment=True)


@api_v1.route("/releases", methods=["GET", "POST"])
@requires_auth(read_scopes=(SCOPE_READ_CONTENT, SCOPE_READ_RELEASES))
def releases() -> ResponseType:
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

        dbc = db.get_db()
        c = dbc.cursor()

        try:
            c.execute("BEGIN TRANSACTION")  # Put SQLite into manual commit mode
            # First insert the row with no bundle create, to trigger any early errors and rollback if necessary
            # without wasting disk space.
            r = db.set_release(None, r, commit=False)
            r["bundle_size"] = make_release_bundle(r, bundle_path)  # Side effect: write bundle file
            r = db.set_release(r["version"], r, commit=False)  # Update release row with bundle size
            dbc.commit()  # Finally, commit
        except Exception as e:
            print("Warning: encountered exception while making bundle", e, file=sys.stderr)
            traceback.print_exc()
            dbc.rollback()
            return {
                "message": "Error encountered while generating release",
                "errors": [traceback.format_exc()],
            }, 500

        return jsonify(r)

    return jsonify(db.get_releases())


@api_v1.route("/releases/<int:version>", methods=["GET", "PUT"])
@requires_auth(read_scopes=(SCOPE_READ_CONTENT, SCOPE_READ_RELEASES),
               alter_scopes=(SCOPE_MANAGE_CONTENT, SCOPE_EDIT_RELEASES))
def releases_detail(version: int) -> ResponseType:
    r = db.get_release(version)

    if r is None:
        return {"message": f"Could not find release {version}"}, 404

    if request.method == "PUT":  # non-standard: don't allow PUT if release does not already exist
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request_changed(r["version"]):
            return err_cannot_alter_id

        if request_changed(r["bundle_path"], field="bundle_path"):
            return {"message": f"Cannot alter bundle path"}, 400

        if request_changed(r["submitted_dt"], field="submitted_dt"):
            return {"message": f"Cannot alter submitted date/time"}, 400

        published_dt = request.json.get("published_dt")
        published = request.json.get("published")  # Alternate boolean field - signal to generate published_dt timestamp
        if r["published_dt"] is None and (published_dt or published):
            # Overwrite user-set published time if it exists
            published_dt = get_utc_str()

        r = {**r, **request.json, "published_dt": published_dt}

        if errs := list(release_validator.iter_errors(r)):
            return err_validation_failed(errs)

        r = db.set_release(version, r)

    return jsonify(r)


@api_v1.route("/releases/<int:version>/bundle", methods=["GET"])
@requires_auth(read_scopes=(SCOPE_READ_CONTENT, SCOPE_READ_RELEASES))
def releases_bundle(version: int) -> ResponseType:
    r = db.get_release(version)

    if r is None:
        return {"message": f"Could not find release {version}"}, 404

    return send_file(
        r["bundle_path"], mimetype="application/zip", as_attachment=True, download_name=f"version_{r['version']}.zip")


@api_v1.route("/releases/latest", methods=["GET"])
@requires_auth(read_scopes=(SCOPE_READ_CONTENT, SCOPE_READ_RELEASES))
def latest_release() -> ResponseType:
    r = db.get_latest_release()

    if r is None:
        return {"message": f"No releases exist"}, 404

    return jsonify(r)


@api_v1.route("/search", methods=["GET"])
@requires_auth()
def search() -> ResponseType:
    q = request.args.get("q", "").strip()

    if not q:
        return {"message": "No query specified"}, 400

    return {
        "modals": db.modal_model.search(q),
        "pages": db.page_model.search(q),
        "stations": db.station_model.search(q),
    }


@api_v1.route("/settings", methods=["GET", "PUT"])
@requires_auth()
def settings() -> ResponseType:
    s: dict = db.get_settings()

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        s = db.set_settings({str(k): v for k, v in request.json.items()})

    return jsonify(s)


@api_v1.route("/feedback", methods=["GET", "POST"])
@requires_auth()
def feedback() -> ResponseType:
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

        return jsonify(db.set_feedback_item(f["id"], f))

    return jsonify(db.get_feedback_items())


@api_v1.route("/ott", methods=["POST"])
@requires_auth()
def ott() -> ResponseType:
    new_token = str(uuid.uuid4())
    t = {
        "token": new_token,
        "scope": SCOPE_READ_CONTENT,  # Currently: ignore Bearer scope
        "expiry": (datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc) + timedelta(seconds=60)).isoformat()
    }
    return jsonify(db.set_ott(new_token, t))


# TODO: Move this into app web distribution
@well_known.route("/apple-app-site-association")
def asaa() -> ResponseType:
    return {
        "applinks": {
            "apps": [],
            "details": [{
                "appID": current_app.config["APPLE_APP_ID"],
                "paths": [
                    "/modals/*",
                    "/pages/*",
                    "/stations/detail/*",
                ],
            }],
        },
    }


# TODO: move this into app web distribution
@well_known.route("/assetlinks.json")
def android_asset_links() -> ResponseType:
    return jsonify([{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": current_app.config["ANDROID_PACKAGE_NAME"],
            "sha256_cert_fingerprints": [current_app.config["ANDROID_CERT_FINGERPRINT"]],
        },
    }])

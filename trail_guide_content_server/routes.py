import uuid

from flask import Blueprint, jsonify, current_app, request

from .db import (
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
from .object_schemas import section_validator, station_validator, modal_validator

__all__ = ["api_v1"]

api_v1 = Blueprint("api", __name__)

err_must_be_object = current_app.response_class(jsonify({"message": "Request body must be an object"}), status=400)
err_cannot_alter_id = current_app.response_class(jsonify({"message": "Cannot alter object ID"}), status=400)


def err_validation_failed(errs):
    return current_app.response_class(jsonify({"message": "Object validation failed", "errors": errs}))


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
        return current_app.response_class(jsonify(
            {"message": f"Could not find section with ID {section_id}"}), status=404)

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request.json.get("id") != s["id"]:
            return err_cannot_alter_id

        s = {**s, **request.json}

        errs = list(section_validator.iter_errors(s))
        if errs:
            return current_app.response_class(jsonify({"message": "Object validation failed", "errors": errs}))

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
        return current_app.response_class(jsonify(
            {"message": f"Could not find station with ID {station_id}"}), status=404)

    # TODO: Delete
    if request.method == "DELETE":
        delete_station(station_id)
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request.json.get("id") != s["id"]:
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


@api_v1.route("/assets", methods=["GET", "POST"])
def assets():
    if request.method == "POST":
        # TODO
        # multipart form data, since we need to allow file uploads
        # TODO: maximum upload size
        return

    return jsonify(get_assets())


@api_v1.route("/assets/<string:asset_id>", methods=["GET", "PUT", "DELETE"])
def assets_detail(asset_id):
    a = get_asset(asset_id)

    if a is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find asset with ID {asset_id}"}), status=404)

    if request.method == "DELETE":
        # TODO: Delete object and bytes
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        if not isinstance(request.json, dict):
            return err_must_be_object

        if request.json.get("id") != a["id"]:
            return err_cannot_alter_id

        # TODO: Validate resulting object
        a = {**a, **request.json}
        # TODO: Put to DB

    return jsonify(a)


@api_v1.route("/assets/<string:asset_id>/bytes", methods=["GET", "PUT"])
def assets_bytes(asset_id: str):
    if request.method == "PUT":
        # TODO
        pass

    return b""  # TODO: Streaming response


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

        if request.json.get("id") != p["id"]:
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

from flask import Blueprint, jsonify, current_app, request

from .db import (
    get_categories,

    get_sections,
    get_sections_with_stations,
    get_stations,

    get_asset_types,
    get_assets,
    get_asset,

    get_pages,
    get_modals,
    get_modal,

    get_settings,
)

__all__ = ["api_v1"]

api_v1 = Blueprint("api", __name__)


@api_v1.route("/categories", methods=["GET"])
def categories():
    return jsonify(get_categories())


@api_v1.route("/sections", methods=["GET"])
def sections():
    nest_stations = request.args.get("nest_stations")
    return jsonify(get_sections_with_stations() if nest_stations else get_sections())

# TODO: Section detail


@api_v1.route("/stations", methods=["GET", "POST"])
def stations():
    if request.method == "POST":
        # TODO: Create station
        return

    return jsonify(get_stations())

# TODO: Station detail


@api_v1.route("/asset_types", methods=["GET"])
def asset_types():
    return jsonify(get_asset_types())


@api_v1.route("/assets", methods=["GET", "POST"])
def assets():
    if request.method == "POST":
        # TODO
        return

    return jsonify(get_assets())


@api_v1.route("/assets/<string:asset_id>", methods=["GET", "PUT", "DELETE"])
def assets_detail(asset_id):
    a = get_asset(asset_id)

    if a is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find asset with ID {asset_id}"}), status=404)

    if request.method == "DELETE":
        # TODO
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        # TODO: Validate request.json and resulting object
        a = {**a, **request.json}
        # TODO: Put to DB

    return jsonify(a)  # TODO


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
    if request.method == "PUT":
        # TODO
        return

    return jsonify({})  # TODO


@api_v1.route("/modals", methods=["GET", "POST"])
def modals():
    if request.method == "POST":
        # TODO
        return

    return jsonify(get_modals())


@api_v1.route("/modals/<string:modal_id>", methods=["DELETE", "GET", "PUT"])
def modals_detail(modal_id: str):
    m = get_modal(modal_id)

    if m is None:
        return current_app.response_class(jsonify(
            {"message": f"Could not find modal with ID {modal_id}"}), status=404)

    if request.method == "DELETE":
        # TODO
        return jsonify({"message": "Deleted."})

    if request.method == "PUT":
        m = {**m, **request.json}
        # TODO: Put to DB

    return jsonify(m)


@api_v1.route("/settings", methods=["GET", "PUT"])
def settings():
    s = get_settings()

    if request.method == "PUT":
        s = {**s, **{str(k): v for k, v in request.json.items()}}
        # TODO: Put to DB

    return jsonify(s)

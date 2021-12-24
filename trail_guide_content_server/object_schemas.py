# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021  David Lougheed
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import jsonschema

__all__ = [
    "STATION_SCHEMA",
    "station_validator",

    "SECTION_SCHEMA",
    "section_validator",

    "ASSET_SCHEMA",
    "asset_validator",

    "MODAL_SCHEMA",
    "modal_validator",

    "LAYER_SCHEMA",
    "layer_validator",

    "RELEASE_SCHEMA",
    "release_validator",

    "FEEDBACK_ITEM_SCHEMA",
    "feedback_item_validator",
]

STATION_SCHEMA = {
    "type": "object",
    "required": [
        "id", "title", "long_title", "subtitle", "coordinates_utm", "section", "category", "header_image", "contents",
        "enabled", "rank"],
    "properties": {
        "id": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "long_title": {
            "type": "string",
        },
        "subtitle": {
            "type": "string",
        },
        "coordinates_utm": {
            "type": "object",
            "required": ["zone"],
            # TODO: Proper required with east/west and north/south
            "properties": {
                "zone": {
                    "type": "string",
                },
                "east": {
                    "type": "integer",
                },
                "west": {
                    "type": "integer",
                },
                "north": {
                    "type": "integer",
                },
                "south": {
                    "type": "integer",
                },
            }
        },
        "visible": {
            "type": "object",
            "required": ["from", "to"],
            "properties": {
                # TODO: Mandate that either both are null or neither are
                "from": {"type": ["string", "null"]},
                "to": {"type": ["string", "null"]},
            },
        },
        "section": {
            "type": "string",
        },
        "category": {
            "type": "string",
        },
        "header_image": {
            "type": ["string", "null"],
        },
        "contents": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["content_type"],
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": ["html", "quiz", "gallery"],
                    },

                    # TODO: We need proper if/else, but for now just list the different properties

                    # common
                    "title": {
                        "type": "string",
                    },

                    # html
                    "content_before_fold": {
                        "type": "string",
                    },
                    "content_after_fold": {
                        "type": "string",
                    },

                    # gallery
                    "description": {
                        "type": "string",
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "asset": {
                                    "type": "string",
                                },
                                "caption": {
                                    "type": "string",
                                },
                            },
                        },
                    },

                    # quiz
                    "quiz_type": {
                        "type": "string",
                        "enum": ["match_values", "select_all_that_apply", "choose_one"],
                    },
                    "question": {
                        "type": "string",
                    },
                    "answer": {
                        "type": "string",
                    },
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "answer": {
                                    "type": ["boolean", "string"],
                                }
                            },
                        },
                    },
                },
            },
        },
        "enabled": {
            "type": "boolean",
        },
        "rank": {
            "type": "integer",
        },
    }
}

station_validator = jsonschema.Draft7Validator(STATION_SCHEMA)

SECTION_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "rank"],
    "properties": {
        "id": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "rank": {
            "type": "integer",
            "minimum": 0,
        },
    },
}

section_validator = jsonschema.Draft7Validator(SECTION_SCHEMA)

ASSET_SCHEMA = {
    "type": "object",
    "required": ["id", "asset_type", "file_name", "file_size", "sha1_checksum", "enabled"],
    "properties": {
        "id": {
            "type": "string",
            "format": "uuid",
        },
        "asset_type": {
            "type": "string",
            "enum": ["image", "audio", "video"],
        },
        "file_name": {
            "type": "string",
        },
        "file_size": {
            "type": "integer",
            "minimum": 0,
        },
        "sha1_checksum": {
            "type": "string",
            "minLength": 40,
            "maxLength": 40,
        },
        "enabled": {
            "type": "boolean",
        },
    },
}

asset_validator = jsonschema.Draft7Validator(ASSET_SCHEMA)

MODAL_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "content", "close_text"],
    "properties": {
        "id": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "content": {
            "type": "string",
        },
        "close_text": {
            "type": "string",
        },
    },
}

modal_validator = jsonschema.Draft7Validator(MODAL_SCHEMA)

LAYER_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "geojson", "enabled", "rank"],
    "properties": {
        "id": {
            "type": "string",
        },
        "name": {
            "type": "string",
        },
        "geojson": {
            "type": "object",
        },
        "enabled": {
            "type": "boolean",
        },
        "rank": {
            "type": "integer",
        },
    },
}

layer_validator = jsonschema.Draft7Validator(LAYER_SCHEMA)

RELEASE_SCHEMA = {
    "type": "object",
    "required": ["version", "release_notes", "bundle_path", "submitted_dt"],
    "properties": {
        "version": {
            "type": "integer",
        },
        "release_notes": {
            "type": "string",
        },
        "bundle_path": {
            "type": "string",
        },
        "submitted_dt": {
            "type": "string",
        },
        "published_dt": {
            "type": ["string", "null"],
        },
    }
}

release_validator = jsonschema.Draft7Validator(RELEASE_SCHEMA)

SETTINGS_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": ["string", "null"],
    },
}

settings_validator = jsonschema.Draft7Validator(SETTINGS_SCHEMA)

FEEDBACK_ITEM_SCHEMA = {
    "type": "object",
    "required": ["id"],
    "properties": {
        "from": {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            }
        },
        "content": {"type": "string"},
        "submitted": {"type": "string"},
    }
}

feedback_item_validator = jsonschema.Draft7Validator(FEEDBACK_ITEM_SCHEMA)

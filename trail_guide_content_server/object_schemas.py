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
]

STATION_SCHEMA = {
    "type": "object",
    "required": [
        "id", "title", "long_title", "subtitle", "coordinates_utm", "section", "category", "header_image", "contents",
        "enabled"],
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

                    # html
                    "content_before_fold": {
                        "type": "string",
                    },
                    "content_after_fold": {
                        "type": "string,"
                    },

                    # quiz
                    "quiz_type": {
                        "type": "string",
                        "enum": ["match_values", "select_all_that_apply", "choose_one"],
                    },
                    "content": {
                        "type": "string",
                    },
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
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
    "required": ["id", "asset_type", "file_name", "file_size"],
    "properties": {
        "id": {
            "type": "string",
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

SETTINGS_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": ["string", "null"],
    },
}

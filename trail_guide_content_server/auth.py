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

import jwt
from flask import current_app, g, request
from functools import wraps
from typing import Optional

__all__ = [
    "SCOPE_READ_CONTENT",
    "SCOPE_MANAGE_CONTENT",
    "AuthError",
    "requires_auth",
]


SCOPE_READ_CONTENT = "read:content"
SCOPE_MANAGE_CONTENT = "manage:content"


class AuthError(Exception):
    def __init__(self, message: str, errors: list[str]):
        self.message = message
        self.errors = errors

    def __iter__(self):
        yield "message", self.message
        yield "errors", self.errors


def get_jwks_client() -> jwt.PyJWKClient:
    jwks_client = getattr(g, "_jwks_client", None)
    if jwks_client is None:
        jwks_client = g._jwks_client = jwt.PyJWKClient(current_app.config["AUTH_ISSUER"] + ".well-known/jwks.json")
    return jwks_client


def _get_bearer() -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header:
        token_info = auth_header.split(" ")
        if len(token_info) != 2 or token_info[0] != "Bearer":
            raise AuthError("Unauthorized", ["Invalid authorization header"])

        token = token_info[-1]

    return token


def requires_auth(fn):
    @wraps(fn)
    def _requires_auth(*args, **kwargs):
        token = _get_bearer()

        if not token:
            raise AuthError("Unauthorized", ["No bearer token"])

        jwks_client = get_jwks_client()

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except jwt.PyJWKClientError:
            raise AuthError("Unauthorized", ["JWKS error"])

        try:
            token_data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=current_app.config["AUTH_AUDIENCE"],
            )

        except jwt.ExpiredSignatureError:
            raise AuthError("Unauthorized", ["Expired signature"])

        except jwt.PyJWTError:
            raise AuthError("Unauthorized", ["Token error"])

        if (iss := token_data.get("iss")) != current_app.config["AUTH_ISSUER"]:
            raise AuthError("Unauthorized", [f"Bad issuer: {iss}"])

        scopes = token_data.get("scope", "").split()
        if request.method in ("GET", "HEAD") and SCOPE_READ_CONTENT not in scopes:
            raise AuthError("Unauthorized", [f"Missing scope: {SCOPE_READ_CONTENT}"])
        elif SCOPE_MANAGE_CONTENT not in scopes:
            raise AuthError("Unauthorized", [f"Missing scope: {SCOPE_MANAGE_CONTENT}"])

        return fn(*args, **kwargs)

    return _requires_auth

# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2025  David Lougheed
# See NOTICE for more information.

import jwt
from datetime import datetime, timezone
from flask import current_app, g, request
from functools import wraps
from typing import Optional

from .db import get_ott

__all__ = [
    "SCOPE_READ_CONTENT",
    "SCOPE_MANAGE_CONTENT",
    "SCOPE_READ_RELEASES",
    "SCOPE_EDIT_RELEASES",
    "AuthError",
    "requires_auth",
]


SCOPE_READ_CONTENT = "read:content"
SCOPE_MANAGE_CONTENT = "manage:content"
SCOPE_READ_RELEASES = "read:releases"
SCOPE_EDIT_RELEASES = "edit:releases"


class AuthError(Exception):
    def __init__(self, message: str, errors: list[str]):
        self.message = message
        self.errors = errors

    def __iter__(self):
        yield "message", self.message
        yield "errors", self.errors


def get_jwks_client() -> jwt.PyJWKClient:
    if (jwks_client := getattr(g, "_jwks_client", None)) is None:
        jwks_client = g._jwks_client = jwt.PyJWKClient(current_app.config["AUTH_ISSUER"] + ".well-known/jwks.json")
    return jwks_client


def _get_bearer() -> Optional[str]:
    token = None

    if auth_header := request.headers.get("Authorization"):
        token_info = auth_header.split(" ")
        if len(token_info) != 2 or token_info[0] != "Bearer":
            raise AuthError("Unauthorized", ["Invalid authorization header"])

        token = token_info[-1]

    return token


def _check_scope(scope, read_scopes, alter_scopes):
    scopes = scope.split()

    if request.method in ("GET", "HEAD"):
        if not any(s in scopes for s in read_scopes):
            raise AuthError("Unauthorized", [f"Missing scope: {read_scopes.join(' or ')}"])
        return

    elif not any(s in scopes for s in alter_scopes):
        raise AuthError("Unauthorized", [f"Missing scope: {alter_scopes.join(' or ')}"])


def requires_auth(read_scopes=(SCOPE_READ_CONTENT,), alter_scopes=(SCOPE_MANAGE_CONTENT,)):
    def requires_auth_dec(fn):
        @wraps(fn)
        def _requires_auth(*args, **kwargs):
            # If we're in debug mode, skip this whole deal

            if current_app.debug:
                return fn(*args, **kwargs)

            # First, check for one-time tokens

            if (ott := request.args.get("ott")) is not None:
                ott_data = get_ott(ott)
                ott_expiry = datetime.fromisoformat(ott_data["expiry"])

                if datetime.utcnow().replace(tzinfo=timezone.utc) > ott_expiry:
                    raise AuthError("Unauthorized", ["Expired one-time token"])

                _check_scope(ott_data["scope"], read_scopes, alter_scopes)

                return fn(*args, **kwargs)

            # Then, handle 'real' bearer tokens

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

            _check_scope(token_data.get("scope", ""), read_scopes, alter_scopes)

            return fn(*args, **kwargs)

        return _requires_auth

    return requires_auth_dec

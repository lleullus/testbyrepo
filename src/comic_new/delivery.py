"""Delivery service, Blogger adapter protocol, and destination readback.

Implements BLOCK-05:
- Release Authorization validation and preflight
- All-or-Nothing integrity gates (5-cut current, artifact closure, physical assets)
- Lossless PNG Export (atomic zero-reflow byte copying)
- Blogger delivery adapter protocol, controlled test harness, and destination readback
- Independent transactions for delivery attempt start and outcome recording (no SQLite lock during external I/O)
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile
import time
from typing import Any, Protocol
import urllib.error
import urllib.parse
import urllib.request
from PIL import Image

from comic_new.composition import CANONICAL_WIDTH
from comic_new.composition_service import (
    ArtifactReadbackError,
    CompositionService,
    MaterializedArtifact,
)
from comic_new.store import (
    AuthorizationRevokedError,
    ConflictError,
    InvalidArtifactClosureError,
    RealizationIncompleteError,
    TransactionalStore,
    ValidationError,
)


class DeliveryError(Exception):
    """Base error for delivery and release failures."""


class ReleasePreflightError(DeliveryError):
    """Raised when all-or-nothing release preflight fails."""


class SourceAssetMissingError(DeliveryError):
    """Raised when a canonical physical asset or review artifact is missing or corrupted."""


class BloggerTransportTimeoutError(DeliveryError):
    """Raised when Blogger transport times out, disconnects, or gives an incomplete response.

    May carry provisional post_id, destination_url, and raw_response if insert succeeded but readback was ambiguous.
    """

    def __init__(
        self,
        message: str,
        *,
        post_id: str | None = None,
        destination_url: str | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.post_id = post_id
        self.destination_url = destination_url
        self.raw_response = raw_response


class BloggerAuthoritativeError(DeliveryError):
    """Raised when Blogger definitively rejects the delivery request (e.g. 401, 400)."""

    def __init__(self, status_code: int, message: str, details: Any = None) -> None:
        super().__init__(f"Blogger rejected request ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.details = details


class BloggerContentIdentityError(DeliveryError):
    """Raised when destination readback fails content identity verification (e.g. missing, malformed, duplicate, or mismatched marker)."""

    def __init__(
        self,
        reason: str,
        *,
        expected_artifact_id: str,
        expected_sha256: str,
        observed_marker: str | None = None,
        details: Any = None,
        post_id: str | None = None,
        destination_url: str | None = None,
    ) -> None:
        super().__init__(f"Blogger content identity verification failed ({reason})")
        self.reason = reason
        self.expected_artifact_id = expected_artifact_id
        self.expected_sha256 = expected_sha256
        self.observed_marker = observed_marker
        self.details = details
        self.post_id = post_id
        self.destination_url = destination_url


@dataclass(frozen=True)
class VerifiedArtifactPayload:
    authorization_id: str
    artifact_id: str
    content_hash: str
    png_bytes: bytes
    filename: str


@dataclass(frozen=True)
class BloggerPublishResult:
    post_id: str
    destination_url: str
    raw_response: dict[str, Any]
    readback_evidence: dict[str, Any]


def format_blogger_marker(artifact_id: str, sha256: str) -> str:
    """Format the canonical Blogger identity marker comment."""
    return f"<!-- comic-new:artifact-id={artifact_id}:sha256={sha256} -->"


import re
from html.parser import HTMLParser

_EXACT_MARKER_REGEX = re.compile(
    r"^<!--\s*comic-new:artifact-id=([a-zA-Z0-9_-]+):sha256=([a-fA-F0-9]{64})\s*-->$"
)


class _CommentExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.comments: list[str] = []

    def handle_comment(self, data: str) -> None:
        self.comments.append(data.strip())


def parse_blogger_markers(html_body: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Extract all HTML comments in body and inspect comments starting with 'comic-new:'.

    Returns (valid_markers, malformed_markers) where valid_markers is a list of (artifact_id, sha256) tuples,
    and malformed_markers is a list of comment strings that begin with 'comic-new:' but don't match exact syntax.
    """
    parser = _CommentExtractor()
    try:
        parser.feed(html_body)
    except Exception:
        pass

    valid: list[tuple[str, str]] = []
    malformed: list[str] = []
    for comment in parser.comments:
        if comment.startswith("comic-new:"):
            # Must match exact pattern inside <!-- ... -->
            full_comment = f"<!-- {comment} -->"
            m = _EXACT_MARKER_REGEX.match(full_comment)
            if m:
                valid.append((m.group(1), m.group(2).lower()))
            else:
                malformed.append(comment)
    return valid, malformed


class BloggerAdapter(Protocol):
    def publish(
        self,
        blog_id: str,
        title: str,
        payload: VerifiedArtifactPayload,
    ) -> BloggerPublishResult:
        ...

    def readback(
        self,
        destination_url: str,
        expected_artifact_id: str,
        expected_content_hash: str,
    ) -> dict[str, Any]:
        ...
class GoogleBloggerAdapter:
    """Production Google Blogger API v3 adapter using OAuth2/token exchange, posts insert, and destination readback."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        token_url: str | None = None,
        api_base_url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._token_url = token_url
        self._api_base_url = api_base_url
        self.timeout_seconds = timeout_seconds

    @property
    def access_token(self) -> str | None:
        return self._access_token or os.environ.get("BLOGGER_ACCESS_TOKEN")

    @property
    def client_id(self) -> str | None:
        return self._client_id or os.environ.get("BLOGGER_CLIENT_ID")

    @property
    def client_secret(self) -> str | None:
        return self._client_secret or os.environ.get("BLOGGER_CLIENT_SECRET")

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token or os.environ.get("BLOGGER_REFRESH_TOKEN")

    @property
    def token_url(self) -> str:
        return (
            self._token_url
            or os.environ.get("BLOGGER_TOKEN_URL")
            or "https://oauth2.googleapis.com/token"
        )

    @property
    def api_base_url(self) -> str:
        return (
            self._api_base_url
            or os.environ.get("BLOGGER_API_BASE_URL")
            or "https://www.googleapis.com/blogger/v3"
        )

    def _resolve_access_token(self) -> str:
        """Resolve Bearer access token directly from configuration or via OAuth2 refresh token exchange."""
        token = self.access_token
        if token and token.strip():
            return token.strip()

        refresh_token = self.refresh_token
        client_id = self.client_id
        client_secret = self.client_secret
        if refresh_token and client_id and client_secret:
            return self._exchange_refresh_token(client_id.strip(), client_secret.strip(), refresh_token.strip())

        raise BloggerAuthoritativeError(
            401,
            "Missing Blogger credentials: set BLOGGER_ACCESS_TOKEN or BLOGGER_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN",
            details={"configured": False},
        )

    def _exchange_refresh_token(self, client_id: str, client_secret: str, refresh_token: str) -> str:
        post_data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.token_url,
            data=post_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": "comic-new-delivery/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))
                token = data.get("access_token")
                if not token or not isinstance(token, str):
                    raise BloggerAuthoritativeError(
                        502,
                        "OAuth2 token exchange response missing 'access_token'",
                        details=data,
                    )
                return token.strip()
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode("utf-8", errors="replace")
            except (http.client.IncompleteRead, socket.timeout, TimeoutError, OSError):
                err_body = ""
            try:
                err_details = json.loads(err_body)
            except Exception:
                err_details = {"body": err_body}
            if 400 <= he.code < 500:
                raise BloggerAuthoritativeError(
                    he.code,
                    f"OAuth2 token exchange rejected ({he.code}): {err_body}",
                    details=err_details,
                )
            raise BloggerTransportTimeoutError(
                f"OAuth2 token endpoint returned ambiguous server error ({he.code}): {err_body}"
            )
        except BloggerAuthoritativeError:
            raise
        except http.client.IncompleteRead as ire:
            raise BloggerTransportTimeoutError(f"OAuth2 token exchange incomplete read: {ire}")
        except Exception as e:
            raise BloggerTransportTimeoutError(f"OAuth2 token exchange ambiguous transport error: {e}")

    def publish(
        self,
        blog_id: str,
        title: str,
        payload: VerifiedArtifactPayload,
    ) -> BloggerPublishResult:
        if not blog_id.strip():
            raise BloggerAuthoritativeError(
                400,
                "Missing Blogger blog id: pass blog_id or set BLOGGER_BLOG_ID",
                details={"configured": False},
            )
        token = self._resolve_access_token()

        img_b64 = base64.b64encode(payload.png_bytes).decode("ascii")
        marker = format_blogger_marker(payload.artifact_id, payload.content_hash)
        content_html = f'{marker}\n<p><img src="data:image/png;base64,{img_b64}" alt="{payload.filename}"/></p>'
        request_payload = {
            "kind": "blogger#post",
            "title": title,
            "content": content_html,
        }
        body_bytes = json.dumps(request_payload).encode("utf-8")

        posts_endpoint = f"{self.api_base_url.rstrip('/')}/blogs/{blog_id}/posts"
        req = urllib.request.Request(
            posts_endpoint,
            data=body_bytes,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "comic-new-delivery/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_bytes = resp.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode("utf-8", errors="replace")
            except (http.client.IncompleteRead, socket.timeout, TimeoutError, OSError):
                err_body = ""
            try:
                err_details = json.loads(err_body)
            except Exception:
                err_details = {"body": err_body}
            if 400 <= he.code < 500:
                raise BloggerAuthoritativeError(
                    he.code,
                    f"Blogger post insert rejected ({he.code}): {err_body}",
                    details=err_details,
                )
            raise BloggerTransportTimeoutError(
                f"Blogger post insert returned ambiguous server error ({he.code}): {err_body}"
            )
        except BloggerAuthoritativeError:
            raise
        except http.client.IncompleteRead as ire:
            raise BloggerTransportTimeoutError(f"Blogger post insert incomplete read: {ire}")
        except Exception as e:
            raise BloggerTransportTimeoutError(f"Blogger post insert ambiguous transport error: {e}")

        post_id = resp_json.get("id")
        destination_url = resp_json.get("url")
        if not post_id or not destination_url:
            raise BloggerTransportTimeoutError(
                "Blogger post insert response omitted the required 'id' or 'url' fields"
            )

        # Destination URL GET readback for content identity
        try:
            evidence = self.readback(
                str(destination_url),
                expected_artifact_id=payload.artifact_id,
                expected_content_hash=payload.content_hash,
            )
        except BloggerContentIdentityError as cie:
            cie.post_id = str(post_id)
            cie.destination_url = str(destination_url)
            raise cie
        except BloggerAuthoritativeError as ae:
            # 4xx on destination readback is definitive failure
            raise BloggerContentIdentityError(
                f"Destination HTTP {ae.status_code}",
                expected_artifact_id=payload.artifact_id,
                expected_sha256=payload.content_hash,
                details=ae.details,
                post_id=str(post_id),
                destination_url=str(destination_url),
            ) from ae
        except BloggerTransportTimeoutError as te:
            # Attach provisional destination info to the transport error!
            if te.post_id is None:
                te.post_id = str(post_id)
            if te.destination_url is None:
                te.destination_url = str(destination_url)
            if te.raw_response is None:
                te.raw_response = resp_json
            raise te
        except Exception as e:
            raise BloggerTransportTimeoutError(
                f"Destination URL readback ambiguous transport error: {e}",
                post_id=str(post_id),
                destination_url=str(destination_url),
                raw_response=resp_json,
            ) from e

        return BloggerPublishResult(
            post_id=str(post_id),
            destination_url=str(destination_url),
            raw_response=resp_json,
            readback_evidence=evidence,
        )

    def readback(
        self,
        destination_url: str,
        expected_artifact_id: str,
        expected_content_hash: str,
    ) -> dict[str, Any]:
        readback_req = urllib.request.Request(
            destination_url,
            headers={
                "User-Agent": "comic-new-delivery/1.0",
                "Accept": "*/*",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(readback_req, timeout=self.timeout_seconds) as rb_resp:
                body_bytes = rb_resp.read()
                html_body = body_bytes.decode("utf-8")
        except urllib.error.HTTPError as he:
            try:
                err_body = he.read().decode("utf-8", errors="replace")
            except (http.client.IncompleteRead, socket.timeout, TimeoutError, OSError):
                err_body = ""
            if 400 <= he.code < 500:
                raise BloggerAuthoritativeError(
                    he.code,
                    f"Destination URL readback rejected ({he.code}): {destination_url}",
                    details={"body": err_body},
                )
            raise BloggerTransportTimeoutError(
                f"Destination URL readback returned ambiguous server error ({he.code}): {destination_url}"
            )
        except BloggerAuthoritativeError:
            raise
        except http.client.IncompleteRead as ire:
            raise BloggerTransportTimeoutError(f"Destination URL readback incomplete read: {ire}")
        except Exception as exc:
            raise BloggerTransportTimeoutError(f"Destination URL readback ambiguous transport error: {exc}")


        valid_markers, malformed_markers = parse_blogger_markers(html_body)
        if malformed_markers:
            raise BloggerContentIdentityError(
                "malformed_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                details={"malformed_comments": malformed_markers},
            )
        if len(valid_markers) == 0:
            raise BloggerContentIdentityError(
                "missing_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
            )
        if len(valid_markers) > 1:
            raise BloggerContentIdentityError(
                "duplicate_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                details={"observed_markers": [format_blogger_marker(a, s) for a, s in valid_markers]},
            )

        observed_art_id, observed_hash = valid_markers[0]
        if observed_art_id != expected_artifact_id:
            raise BloggerContentIdentityError(
                "artifact_id_mismatch",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                observed_marker=format_blogger_marker(observed_art_id, observed_hash),
                details={"observed_artifact_id": observed_art_id},
            )
        if observed_hash.lower() != expected_content_hash.lower():
            raise BloggerContentIdentityError(
                "content_hash_mismatch",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                observed_marker=format_blogger_marker(observed_art_id, observed_hash),
                details={"observed_sha256": observed_hash},
            )

        return {
            "marker_verified": True,
            "expected_artifact_id": expected_artifact_id,
            "expected_sha256": expected_content_hash,
            "observed_artifact_id": observed_art_id,
            "observed_sha256": observed_hash,
            "destination_url": destination_url,
            "body_length": len(body_bytes),
        }

class ControlledBloggerAdapter:
    """Deterministic test adapter supporting success, content identity discrimination, timeout, disconnect, and auth failure modes."""

    def __init__(
        self,
        mode: str = "success",
        *,
        delay_seconds: float = 0.0,
        post_id: str = "post-blogger-default",
        destination_url: str = "https://comic.blogspot.com/2026/09/episode-1.html",
        error_status: int = 400,
        error_message: str = "Bad Request",
        readback_mode: str | None = None,
    ) -> None:
        self.mode = mode
        self.delay_seconds = delay_seconds
        self.post_id = post_id
        self.destination_url = destination_url
        self.error_status = error_status
        self.error_message = error_message
        self.readback_mode = readback_mode
        self.calls: list[dict[str, Any]] = []
        self.readback_calls: list[dict[str, Any]] = []

    def publish(
        self,
        blog_id: str,
        title: str,
        payload: VerifiedArtifactPayload,
    ) -> BloggerPublishResult:
        if not blog_id or not blog_id.strip():
            raise BloggerAuthoritativeError(
                400,
                "Missing Blogger blog id: pass blog_id or set BLOGGER_BLOG_ID",
                details={"configured": False},
            )
        call_record = {
            "blog_id": blog_id,
            "title": title,
            "bytes_len": len(payload.png_bytes),
            "filename": payload.filename,
            "artifact_id": payload.artifact_id,
            "content_hash": payload.content_hash,
            "mode": self.mode,
        }
        self.calls.append(call_record)

        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        # Pre-destination failures (e.g. insert failed or insert timeout before post identity known)
        if self.mode == "timeout":
            raise BloggerTransportTimeoutError("Blogger transport timed out waiting for response")
        elif self.mode == "disconnect":
            raise BloggerTransportTimeoutError("Connection closed unexpectedly by Blogger remote peer")
        elif self.mode == "incomplete_read":
            raise BloggerTransportTimeoutError("Blogger transport incomplete read")
        elif self.mode in ("auth_failure", "bad_request", "error"):
            status = 401 if self.mode == "auth_failure" else self.error_status
            msg = "Unauthorized" if self.mode == "auth_failure" else self.error_message
            raise BloggerAuthoritativeError(status, msg, {"mode": self.mode})

        # Insert succeeded; post_id and destination_url are now known
        raw_response = {
            "kind": "blogger#post",
            "id": self.post_id,
            "url": self.destination_url,
            "title": title,
            "blog": {"id": blog_id},
            "status": "LIVE",
        }

        # Destination readback
        effective_rb_mode = self.readback_mode or self.mode
        try:
            readback_evidence = self._execute_readback_mode(
                effective_rb_mode,
                self.destination_url,
                payload.artifact_id,
                payload.content_hash,
            )
        except BloggerTransportTimeoutError as te:
            raise BloggerTransportTimeoutError(
                str(te),
                post_id=self.post_id,
                destination_url=self.destination_url,
                raw_response=raw_response,
            ) from te
        except BloggerAuthoritativeError as ae:
            raise BloggerContentIdentityError(
                f"Destination HTTP {ae.status_code}",
                expected_artifact_id=payload.artifact_id,
                expected_sha256=payload.content_hash,
                details=ae.details,
                post_id=self.post_id,
                destination_url=self.destination_url,
            ) from ae
        except BloggerContentIdentityError as cie:
            cie.post_id = self.post_id
            cie.destination_url = self.destination_url
            raise cie

        return BloggerPublishResult(
            post_id=self.post_id,
            destination_url=self.destination_url,
            raw_response=raw_response,
            readback_evidence=readback_evidence,
        )

    def readback(
        self,
        destination_url: str,
        expected_artifact_id: str,
        expected_content_hash: str,
    ) -> dict[str, Any]:
        effective_rb_mode = self.readback_mode or self.mode
        return self._execute_readback_mode(
            effective_rb_mode,
            destination_url,
            expected_artifact_id,
            expected_content_hash,
        )

    def _execute_readback_mode(
        self,
        rb_mode: str,
        destination_url: str,
        expected_artifact_id: str,
        expected_content_hash: str,
    ) -> dict[str, Any]:
        self.readback_calls.append({
            "destination_url": destination_url,
            "expected_artifact_id": expected_artifact_id,
            "expected_content_hash": expected_content_hash,
            "rb_mode": rb_mode,
        })
        if rb_mode in ("success", "exact"):
            marker = format_blogger_marker(expected_artifact_id, expected_content_hash)
            return {
                "marker_verified": True,
                "expected_artifact_id": expected_artifact_id,
                "expected_sha256": expected_content_hash,
                "observed_artifact_id": expected_artifact_id,
                "observed_sha256": expected_content_hash,
                "destination_url": destination_url,
                "body_length": len(marker) + 50,
            }
        elif rb_mode == "readback_timeout":
            raise BloggerTransportTimeoutError("Destination URL readback timed out")
        elif rb_mode == "readback_disconnect":
            raise BloggerTransportTimeoutError("Destination URL readback connection reset")
        elif rb_mode == "readback_incomplete_read":
            raise BloggerTransportTimeoutError("Destination URL readback incomplete read")
        elif rb_mode == "readback_404":
            raise BloggerAuthoritativeError(404, f"Destination URL not found: {destination_url}")
        elif rb_mode == "missing_marker":
            raise BloggerContentIdentityError(
                "missing_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
            )
        elif rb_mode == "malformed_marker":
            raise BloggerContentIdentityError(
                "malformed_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                details={"malformed_comments": ["comic-new:broken-marker"]},
            )
        elif rb_mode == "duplicate_marker":
            m1 = format_blogger_marker(expected_artifact_id, expected_content_hash)
            m2 = format_blogger_marker(expected_artifact_id, expected_content_hash)
            raise BloggerContentIdentityError(
                "duplicate_marker",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                details={"observed_markers": [m1, m2]},
            )
        elif rb_mode == "wrong_artifact_id":
            wrong_id = f"{expected_artifact_id}-tampered"
            raise BloggerContentIdentityError(
                "artifact_id_mismatch",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                observed_marker=format_blogger_marker(wrong_id, expected_content_hash),
                details={"observed_artifact_id": wrong_id},
            )
        elif rb_mode == "wrong_hash":
            wrong_hash = "0" * 64
            raise BloggerContentIdentityError(
                "content_hash_mismatch",
                expected_artifact_id=expected_artifact_id,
                expected_sha256=expected_content_hash,
                observed_marker=format_blogger_marker(expected_artifact_id, wrong_hash),
                details={"observed_sha256": wrong_hash},
            )
        else:
            raise ValueError(f"Unknown ControlledBloggerAdapter mode: {rb_mode}")

@dataclass(frozen=True)
class DeliveryResult:
    attempt_id: str
    kind: str
    authorization_id: str
    artifact_id: str
    outcome: str
    destination_id: str | None
    destination_url: str | None
    output_path: str | None
    content_hash: str
    bytes_written: int | None
    evidence: dict[str, Any] | None
    observed_authority_revision: int


class DeliveryService:
    """Core domain service for release preflight, PNG export, and Blogger delivery."""

    def __init__(
        self,
        store: TransactionalStore,
        composition_service: CompositionService | None = None,
        default_blogger_adapter: BloggerAdapter | None = None,
    ) -> None:
        self.store = store
        self.composition_service = composition_service
        self.default_blogger_adapter = default_blogger_adapter or GoogleBloggerAdapter()

    def preflight_release(
        self,
        authorization_id: str | None = None,
    ) -> tuple[dict[str, Any], VerifiedArtifactPayload]:
        """Perform All-or-Nothing preflight checks before any delivery attempt.

        Reads the canonical review artifact once, validates the ordered active-cut closure,
        and captures verified in-memory bytes. Downstream delivery operations consume
        the returned VerifiedArtifactPayload directly without reopening the source file.

        Returns (auth_record, verified_artifact_payload).
        Raises ReleasePreflightError, SourceAssetMissingError, RealizationIncompleteError,
               InvalidArtifactClosureError, AuthorizationRevokedError.
        """
        snap = self.store.snapshot()
        active_auth = snap.get("release_authorization", {}).get("active")
        if not active_auth:
            raise AuthorizationRevokedError("No active release authorization exists")

        if authorization_id and active_auth["authorization_id"] != authorization_id:
            raise AuthorizationRevokedError(
                f"Active authorization {active_auth['authorization_id']} does not match requested {authorization_id}"
            )

        if active_auth.get("revoked_authority_revision") is not None:
            raise AuthorizationRevokedError(
                f"Release authorization {active_auth['authorization_id']} is revoked"
            )

        auth_id = active_auth["authorization_id"]
        artifact_id = active_auth["artifact_id"]
        expected_hash = active_auth["artifact_content_hash"]

        # 1. Active-set current check (all-or-nothing currency gate)
        realization_complete = snap.get("realization_complete", {})
        if not realization_complete.get("complete"):
            raise RealizationIncompleteError("Snapshot realization is incomplete (UNRESOLVED)")
        cuts = snap.get("cuts", [])
        if not cuts:
            raise ReleasePreflightError("Active cut set must not be empty")
        if any(cut.get("currency") != "CURRENT" or cut.get("desired_revision") is None or cut.get("realized_revision") != cut.get("desired_revision") for cut in cuts):
            raise RealizationIncompleteError("All active cuts must have current realizations")

        # 2. Capture verified bytes: prefer CompositionService.read_artifact
        actual_art_bytes: bytes
        art_path = self.store.project_dir / "assets" / "review-artifacts" / f"{artifact_id}.png"
        if self.composition_service is not None:
            try:
                mat = self.composition_service.read_artifact(artifact_id)
                actual_art_bytes = mat.bytes_data
            except Exception as exc:
                raise SourceAssetMissingError(f"Failed to read review artifact via composition service: {exc}") from exc
        else:
            if not art_path.is_file():
                raise SourceAssetMissingError(f"Review artifact file missing at {art_path}")
            actual_art_bytes = art_path.read_bytes()
            try:
                import io
                with Image.open(io.BytesIO(actual_art_bytes)) as im:
                    if im.format != "PNG":
                        raise SourceAssetMissingError(f"Review artifact format {im.format} != PNG")
                    closure_raw = im.text.get("comic_new_closure")
                    if not closure_raw:
                        raise SourceAssetMissingError("Review artifact has no geometry closure")
                    closure = json.loads(closure_raw)
                    expected_size = (closure.get("width_px"), closure.get("height_px"))
                    if expected_size[0] != CANONICAL_WIDTH or not isinstance(expected_size[1], int) or expected_size[1] <= 0 or im.size != expected_size:
                        raise SourceAssetMissingError(f"Review artifact dimensions {im.size} do not match closure {expected_size}")
            except Exception as exc:
                if isinstance(exc, SourceAssetMissingError):
                    raise
                raise SourceAssetMissingError(f"Failed to read review artifact image: {exc}") from exc

        actual_art_hash = hashlib.sha256(actual_art_bytes).hexdigest()
        if actual_art_hash != expected_hash:
            raise SourceAssetMissingError(
                f"Review artifact hash corrupted: expected {expected_hash}, got {actual_art_hash}"
            )

        # 3. Check physical assets for all 5 cuts
        for cut in cuts:
            cid = cut["cut_id"]
            asset_id = cut.get("realized_asset_id")
            raw_path = cut.get("realized_asset_path")
            expected_cut_hash = cut.get("realized_content_hash")
            if not asset_id or not raw_path or not expected_cut_hash:
                raise SourceAssetMissingError(f"Cut {cid} has incomplete realization metadata")

            cut_p = Path(raw_path)
            cut_asset_path = (cut_p if cut_p.is_absolute() else self.store.project_dir / cut_p).resolve()
            if not cut_asset_path.is_file():
                raise SourceAssetMissingError(f"Cut {cid} asset file missing at {cut_asset_path}")
            if cut_asset_path.stat().st_size == 0:
                raise SourceAssetMissingError(f"Cut {cid} asset file is empty: {cut_asset_path}")

            actual_c_bytes = cut_asset_path.read_bytes()
            actual_c_hash = hashlib.sha256(actual_c_bytes).hexdigest()
            if actual_c_hash != expected_cut_hash:
                raise SourceAssetMissingError(
                    f"Cut {cid} hash mismatch: DB has {expected_cut_hash}, file has {actual_c_hash}"
                )
            try:
                with Image.open(cut_asset_path) as c_im:
                    c_im.verify()
            except Exception as exc:
                raise SourceAssetMissingError(f"Cut {cid} asset file is corrupted: {exc}") from exc

        payload = VerifiedArtifactPayload(
            authorization_id=auth_id,
            artifact_id=artifact_id,
            content_hash=expected_hash,
            png_bytes=actual_art_bytes,
            filename=f"comic-{artifact_id}.png",
        )
        return active_auth, payload

    def export_png(
        self,
        expected_authority_revision: int,
        output_path: Path | str | None = None,
        authorization_id: str | None = None,
        attempt_id: str | None = None,
        _post_preflight_hook: Any | None = None,
    ) -> DeliveryResult:
        """Export canonical PNG without reflow, consuming in-memory verified bytes atomically."""
        active_auth, payload = self.preflight_release(authorization_id)
        auth_id = payload.authorization_id
        art_id = payload.artifact_id
        expected_hash = payload.content_hash

        if _post_preflight_hook is not None and callable(_post_preflight_hook):
            _post_preflight_hook()

        dest_path: Path
        if output_path is None:
            exports_dir = self.store.project_dir / "exports"
            exports_dir.mkdir(parents=True, exist_ok=True)
            dest_path = exports_dir / f"comic-{art_id}.png"
        else:
            dest_path = Path(output_path).resolve()

        # Enforce destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        att_id = attempt_id or f"delivery-png-{int(time.time() * 1000)}"
        req_id = f"req-export-{att_id}"

        # 1. Start delivery attempt in SQLite (outcome='unknown')
        start_rev = self.store.start_delivery_attempt(
            expected_authority_revision,
            att_id,
            kind="png",
            authorization_id=auth_id,
            request_id=req_id,
        )

        try:
            # 2. CFW-2 Atomic byte export: write payload.png_bytes to temporary file in same directory then os.replace
            temp_fd, temp_file_str = tempfile.mkstemp(
                prefix=".tmp-export-",
                dir=str(dest_path.parent),
                suffix=".png",
            )
            temp_path = Path(temp_file_str)

            try:
                with os.fdopen(temp_fd, "wb") as f:
                    f.write(payload.png_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, dest_path)
            finally:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

            # 3. Readback verification exclusively from destination
            exported_bytes = dest_path.read_bytes()
            exported_hash = hashlib.sha256(exported_bytes).hexdigest()
            if exported_hash != expected_hash:
                raise DeliveryError(
                    f"Readback hash mismatch: exported {exported_hash} != artifact {expected_hash}"
                )

            with Image.open(dest_path) as im:
                if im.format != "PNG":
                    raise DeliveryError(f"Exported image format mismatch: {im.format}")
                closure_raw = im.text.get("comic_new_closure")
                if not closure_raw:
                    raise DeliveryError("Exported image has no geometry closure")
                closure = json.loads(closure_raw)
                expected_size = (closure.get("width_px"), closure.get("height_px"))
                if expected_size[0] != CANONICAL_WIDTH or not isinstance(expected_size[1], int) or expected_size[1] <= 0 or im.size != expected_size:
                    raise DeliveryError(f"Exported image dimension mismatch: {im.size} vs closure {expected_size}")
                exported_width, exported_height = expected_size
            evidence = {
                "sha256": exported_hash,
                "bytes_written": len(exported_bytes),
                "width": exported_width,
                "height": exported_height,
                "output_path": str(dest_path),
            }

            # 4. Record delivery observation in separate transaction
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="confirmed_success",
                evidence=evidence,
                destination_id=dest_path.name,
                destination_url=dest_path.as_uri(),
            )

            return DeliveryResult(
                attempt_id=att_id,
                kind="png",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_success",
                destination_id=dest_path.name,
                destination_url=dest_path.as_uri(),
                output_path=str(dest_path),
                content_hash=exported_hash,
                bytes_written=len(exported_bytes),
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        except Exception as exc:
            # Try recording confirmed_failure if start succeeded
            try:
                snap = self.store.snapshot()
                cur_rev = snap["authority_revision"]
                self.store.record_delivery_observation(
                    cur_rev,
                    att_id,
                    outcome="confirmed_failure",
                    evidence={"error": str(exc)},
                )
            except Exception:
                pass
            raise

    def deliver_blogger(
        self,
        expected_authority_revision: int,
        blog_id: str | None = None,
        title: str | None = None,
        adapter: BloggerAdapter | None = None,
        authorization_id: str | None = None,
        attempt_id: str | None = None,
        _post_preflight_hook: Any | None = None,
    ) -> DeliveryResult:
        """Deliver comic to Blogger consuming verified in-memory bytes and exact identity marker readback."""
        active_auth, payload = self.preflight_release(authorization_id)
        auth_id = payload.authorization_id
        art_id = payload.artifact_id
        expected_hash = payload.content_hash

        if _post_preflight_hook is not None and callable(_post_preflight_hook):
            _post_preflight_hook()

        att_id = attempt_id or f"delivery-blogger-{int(time.time() * 1000)}"
        req_id = f"req-blogger-{att_id}"
        effective_adapter = adapter or self.default_blogger_adapter

        effective_blog_id = blog_id or os.environ.get("BLOGGER_BLOG_ID") or ""
        effective_title = title or f"Web Comic Episode ({art_id[:8]})"

        # 1. Start delivery attempt (transaction 1 commits 'unknown')
        start_rev = self.store.start_delivery_attempt(
            expected_authority_revision,
            att_id,
            kind="blogger",
            authorization_id=auth_id,
            request_id=req_id,
        )

        # 2. External I/O without any SQLite write lock
        publish_result: BloggerPublishResult | None = None
        transport_error: BloggerTransportTimeoutError | None = None
        auth_error: BloggerAuthoritativeError | None = None
        identity_error: BloggerContentIdentityError | None = None

        try:
            publish_result = effective_adapter.publish(
                effective_blog_id,
                effective_title,
                payload,
            )
        except BloggerContentIdentityError as cie:
            identity_error = cie
        except BloggerAuthoritativeError as ae:
            auth_error = ae
        except BloggerTransportTimeoutError as te:
            transport_error = te
        except http.client.IncompleteRead as ire:
            transport_error = BloggerTransportTimeoutError(f"Blogger delivery incomplete read: {ire}")
        except Exception as e:
            # Category boundary: only explicitly typed BloggerAuthoritativeError and
            # BloggerContentIdentityError may produce confirmed_failure. All other exceptions
            # crossing service adapter boundaries are ambiguous BloggerTransportTimeoutError/unknown.
            post_id = getattr(e, "post_id", None)
            dest_url = getattr(e, "destination_url", None)
            raw_resp = getattr(e, "raw_response", None)
            transport_error = BloggerTransportTimeoutError(
                f"Blogger delivery ambiguous adapter error: {e}",
                post_id=str(post_id) if post_id is not None else None,
                destination_url=str(dest_url) if dest_url is not None else None,
                raw_response=raw_resp,
            )

        # 3. Record delivery observation (transaction 2)
        if publish_result is not None:
            evidence = {
                "post_id": publish_result.post_id,
                "destination_url": publish_result.destination_url,
                "raw_response": publish_result.raw_response,
                "artifact_id": art_id,
                "artifact_hash": expected_hash,
                "readback": publish_result.readback_evidence,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="confirmed_success",
                evidence=evidence,
                destination_id=publish_result.post_id,
                destination_url=publish_result.destination_url,
            )
            return DeliveryResult(
                attempt_id=att_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_success",
                destination_id=publish_result.post_id,
                destination_url=publish_result.destination_url,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=len(payload.png_bytes),
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        elif transport_error is not None:
            # Honest Unknown: retain provisional destination if known, but DO NOT set terminal destination columns
            evidence = {
                "error": "BloggerTransportTimeoutError",
                "message": str(transport_error),
                "artifact_id": art_id,
                "artifact_hash": expected_hash,
                "provisional_post_id": transport_error.post_id,
                "provisional_destination_url": transport_error.destination_url,
                "raw_response": transport_error.raw_response,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="unknown",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=att_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="unknown",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        elif identity_error is not None:
            evidence = {
                "error": "BloggerContentIdentityError",
                "reason": identity_error.reason,
                "expected_artifact_id": identity_error.expected_artifact_id,
                "expected_sha256": identity_error.expected_sha256,
                "observed_marker": identity_error.observed_marker,
                "details": identity_error.details,
                "provisional_post_id": identity_error.post_id,
                "provisional_destination_url": identity_error.destination_url,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="confirmed_failure",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=att_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_failure",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        else:
            assert auth_error is not None
            evidence = {
                "error": "BloggerAuthoritativeError",
                "status_code": auth_error.status_code,
                "message": auth_error.message,
                "details": auth_error.details,
                "artifact_id": art_id,
                "artifact_hash": expected_hash,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="confirmed_failure",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=att_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_failure",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

    def reconcile_blogger(
        self,
        expected_authority_revision: int,
        attempt_id: str,
        adapter: BloggerAdapter | None = None,
    ) -> DeliveryResult:
        """Reconcile an unknown Blogger delivery attempt without republishing.

        1. Reads the exact persisted attempt and enforces kind='blogger' and outcome='unknown'.
        2. Recovers provisional destination_url and artifact identity from the persisted attempt record.
        3. Re-reads remote content using adapter.readback().
        4. Atomically transitions to confirmed_success (exact match) or confirmed_failure (definitive mismatch),
           or refreshes evidence while remaining unknown if transport remains ambiguous.
        """
        attempt = self.store.get_delivery_attempt(attempt_id)
        if not attempt:
            raise ValidationError(f"Delivery attempt {attempt_id} not found")

        if attempt["kind"] != "blogger":
            raise ValidationError(f"Cannot reconcile delivery attempt of kind '{attempt['kind']}' (must be blogger)")

        if attempt["outcome"] != "unknown":
            raise ConflictError(
                expected_authority_revision,
                expected_authority_revision,
                f"Cannot reconcile terminal delivery attempt {attempt_id} (current outcome: {attempt['outcome']})",
            )

        auth_id = attempt["authorization_id"]
        art_id = attempt["artifact_id"]
        expected_hash = attempt["artifact_content_hash"]
        current_evidence = attempt["evidence"] or {}

        # Recover provisional destination from evidence
        destination_url = current_evidence.get("provisional_destination_url") or attempt["destination_url"]
        post_id = current_evidence.get("provisional_post_id") or attempt["destination_id"]

        effective_adapter = adapter or self.default_blogger_adapter

        # If destination is unknown, cannot reconcile without guessing; remain unknown
        if not destination_url:
            evidence = dict(current_evidence)
            evidence["reconcile_status"] = "destination_unknown"
            evidence["reconciled_at"] = time.time()
            obs_rev = self._record_observation_with_retry(
                expected_authority_revision,
                attempt_id,
                outcome="unknown",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=attempt_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="unknown",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        # Perform readback only — NEVER re-insert/publish!
        readback_evidence: dict[str, Any] | None = None
        transport_error: BloggerTransportTimeoutError | None = None
        identity_error: BloggerContentIdentityError | None = None
        auth_error: BloggerAuthoritativeError | None = None

        try:
            readback_evidence = effective_adapter.readback(
                str(destination_url),
                expected_artifact_id=art_id,
                expected_content_hash=expected_hash,
            )
        except BloggerContentIdentityError as cie:
            identity_error = cie
        except BloggerAuthoritativeError as ae:
            auth_error = ae
        except BloggerTransportTimeoutError as te:
            transport_error = te
        except http.client.IncompleteRead as ire:
            transport_error = BloggerTransportTimeoutError(f"Blogger reconcile incomplete read: {ire}")
        except Exception as exc:
            # Category boundary: Reconcile generic adapter/readback failure stays unknown.
            transport_error = BloggerTransportTimeoutError(
                f"Blogger reconcile ambiguous adapter error: {exc}",
                post_id=str(post_id) if post_id is not None else None,
                destination_url=str(destination_url) if destination_url is not None else None,
            )

        if readback_evidence is not None:
            evidence = dict(current_evidence)
            evidence["readback"] = readback_evidence
            evidence["reconciled"] = True
            effective_dest_id = post_id or str(destination_url)
            obs_rev = self._record_observation_with_retry(
                expected_authority_revision,
                attempt_id,
                outcome="confirmed_success",
                evidence=evidence,
                destination_id=effective_dest_id,
                destination_url=str(destination_url),
            )
            return DeliveryResult(
                attempt_id=attempt_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_success",
                destination_id=effective_dest_id,
                destination_url=str(destination_url),
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        elif identity_error is not None:
            evidence = dict(current_evidence)
            evidence["error"] = "BloggerContentIdentityError"
            evidence["reason"] = identity_error.reason
            evidence["expected_artifact_id"] = identity_error.expected_artifact_id
            evidence["expected_sha256"] = identity_error.expected_sha256
            evidence["observed_marker"] = identity_error.observed_marker
            evidence["details"] = identity_error.details
            evidence["reconciled"] = True
            obs_rev = self._record_observation_with_retry(
                expected_authority_revision,
                attempt_id,
                outcome="confirmed_failure",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=attempt_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_failure",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        elif transport_error is not None:
            evidence = dict(current_evidence)
            evidence["reconcile_error"] = str(transport_error)
            evidence["reconciled"] = False
            obs_rev = self._record_observation_with_retry(
                expected_authority_revision,
                attempt_id,
                outcome="unknown",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=attempt_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="unknown",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        else:
            assert auth_error is not None
            evidence = dict(current_evidence)
            evidence["error"] = "BloggerAuthoritativeError"
            evidence["status_code"] = auth_error.status_code
            evidence["message"] = auth_error.message
            evidence["details"] = auth_error.details
            evidence["reconciled"] = True
            obs_rev = self._record_observation_with_retry(
                expected_authority_revision,
                attempt_id,
                outcome="confirmed_failure",
                evidence=evidence,
                destination_id=None,
                destination_url=None,
            )
            return DeliveryResult(
                attempt_id=attempt_id,
                kind="blogger",
                authorization_id=auth_id,
                artifact_id=art_id,
                outcome="confirmed_failure",
                destination_id=None,
                destination_url=None,
                output_path=None,
                content_hash=expected_hash,
                bytes_written=None,
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

    def _record_observation_with_retry(
        self,
        base_revision: int,
        attempt_id: str,
        outcome: str,
        evidence: dict[str, Any] | None = None,
        destination_id: str | None = None,
        destination_url: str | None = None,
    ) -> int:
        """Record observation, retrying with fresh authority revision if concurrent mutation occurred."""
        rev = base_revision
        for _ in range(5):
            try:
                return self.store.record_delivery_observation(
                    rev,
                    attempt_id,
                    outcome=outcome,
                    evidence=evidence,
                    destination_id=destination_id,
                    destination_url=destination_url,
                )
            except ConflictError:
                # Re-check if attempt was already transitioned or not found
                att = self.store.get_delivery_attempt(attempt_id)
                if not att or att["outcome"] != "unknown":
                    raise
                snap = self.store.snapshot()
                rev = snap["authority_revision"]
        # Final attempt with latest
        snap = self.store.snapshot()
        return self.store.record_delivery_observation(
            snap["authority_revision"],
            attempt_id,
            outcome=outcome,
            evidence=evidence,
            destination_id=destination_id,
            destination_url=destination_url,
        )

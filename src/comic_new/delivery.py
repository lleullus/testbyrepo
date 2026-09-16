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

from comic_new.composition import CANONICAL_HEIGHT, CANONICAL_WIDTH
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
    """Raised when Blogger transport times out, disconnects, or gives an incomplete response."""


class BloggerAuthoritativeError(DeliveryError):
    """Raised when Blogger definitively rejects the delivery request (e.g. 401, 400)."""

    def __init__(self, status_code: int, message: str, details: Any = None) -> None:
        super().__init__(f"Blogger rejected request ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class BloggerPublishResult:
    post_id: str
    destination_url: str
    raw_response: dict[str, Any]


class BloggerAdapter(Protocol):
    def publish(
        self,
        blog_id: str,
        title: str,
        artifact_png_bytes: bytes,
        filename: str,
    ) -> BloggerPublishResult:
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
            err_body = he.read().decode("utf-8", errors="replace")
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
        except (socket.timeout, TimeoutError) as te:
            raise BloggerTransportTimeoutError(f"OAuth2 token exchange timed out: {te}")
        except (http.client.RemoteDisconnected, ConnectionResetError, ConnectionRefusedError) as ce:
            raise BloggerTransportTimeoutError(f"OAuth2 token exchange connection error: {ce}")
        except urllib.error.URLError as ue:
            if isinstance(ue.reason, (socket.timeout, TimeoutError, http.client.RemoteDisconnected, ConnectionResetError)):
                raise BloggerTransportTimeoutError(f"OAuth2 token exchange transport timeout: {ue.reason}")
            raise BloggerTransportTimeoutError(f"OAuth2 token exchange network error: {ue.reason}")
        except json.JSONDecodeError as je:
            raise BloggerTransportTimeoutError(
                f"OAuth2 token exchange returned an incomplete response: {je}"
            )

    def publish(
        self,
        blog_id: str,
        title: str,
        artifact_png_bytes: bytes,
        filename: str,
    ) -> BloggerPublishResult:
        if not blog_id.strip():
            raise BloggerAuthoritativeError(
                400,
                "Missing Blogger blog id: pass blog_id or set BLOGGER_BLOG_ID",
                details={"configured": False},
            )
        token = self._resolve_access_token()

        img_b64 = base64.b64encode(artifact_png_bytes).decode("ascii")
        content_html = f'<p><img src="data:image/png;base64,{img_b64}" alt="{filename}"/></p>'
        payload = {
            "kind": "blogger#post",
            "title": title,
            "content": content_html,
        }
        body_bytes = json.dumps(payload).encode("utf-8")

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
            err_body = he.read().decode("utf-8", errors="replace")
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
        except (socket.timeout, TimeoutError) as te:
            raise BloggerTransportTimeoutError(f"Blogger post insert timed out: {te}")
        except (http.client.RemoteDisconnected, ConnectionResetError, ConnectionRefusedError) as ce:
            raise BloggerTransportTimeoutError(f"Blogger post insert connection error: {ce}")
        except urllib.error.URLError as ue:
            if isinstance(ue.reason, (socket.timeout, TimeoutError, http.client.RemoteDisconnected, ConnectionResetError)):
                raise BloggerTransportTimeoutError(f"Blogger post insert transport timeout: {ue.reason}")
            raise BloggerTransportTimeoutError(f"Blogger post insert network error: {ue.reason}")
        except json.JSONDecodeError as je:
            raise BloggerTransportTimeoutError(
                f"Blogger post insert returned an incomplete response: {je}"
            )

        post_id = resp_json.get("id")
        destination_url = resp_json.get("url")
        if not post_id or not destination_url:
            raise BloggerTransportTimeoutError(
                "Blogger post insert response omitted the required 'id' or 'url' fields"
            )

        # Destination URL GET readback
        self._readback_destination(str(destination_url))

        return BloggerPublishResult(
            post_id=str(post_id),
            destination_url=str(destination_url),
            raw_response=resp_json,
        )

    def _readback_destination(self, destination_url: str) -> None:
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
                _ = rb_resp.read()
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="replace")
            if 400 <= he.code < 500:
                raise BloggerAuthoritativeError(
                    he.code,
                    f"Destination URL readback rejected ({he.code}): {destination_url}",
                    details={"body": err_body},
                )
            raise BloggerTransportTimeoutError(
                f"Destination URL readback returned ambiguous server error ({he.code}): {destination_url}"
            )
        except (socket.timeout, TimeoutError) as te:
            raise BloggerTransportTimeoutError(f"Destination URL readback timed out: {te}")
        except (http.client.RemoteDisconnected, ConnectionResetError, ConnectionRefusedError) as ce:
            raise BloggerTransportTimeoutError(f"Destination URL readback connection error: {ce}")
        except urllib.error.URLError as ue:
            if isinstance(ue.reason, (socket.timeout, TimeoutError, http.client.RemoteDisconnected, ConnectionResetError)):
                raise BloggerTransportTimeoutError(f"Destination URL readback transport timeout: {ue.reason}")
            raise BloggerTransportTimeoutError(f"Destination URL readback network error: {ue.reason}")


class ControlledBloggerAdapter:
    """Deterministic test adapter supporting success, timeout, disconnect, and authoritative failure modes."""

    def __init__(
        self,
        mode: str = "success",
        *,
        delay_seconds: float = 0.0,
        post_id: str = "post-blogger-default",
        destination_url: str = "https://comic.blogspot.com/2026/09/episode-1.html",
        error_status: int = 400,
        error_message: str = "Bad Request",
    ) -> None:
        self.mode = mode
        self.delay_seconds = delay_seconds
        self.post_id = post_id
        self.destination_url = destination_url
        self.error_status = error_status
        self.error_message = error_message
        self.calls: list[dict[str, Any]] = []

    def publish(
        self,
        blog_id: str,
        title: str,
        artifact_png_bytes: bytes,
        filename: str,
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
            "bytes_len": len(artifact_png_bytes),
            "filename": filename,
            "mode": self.mode,
        }
        self.calls.append(call_record)

        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        if self.mode == "success":
            raw_response = {
                "kind": "blogger#post",
                "id": self.post_id,
                "url": self.destination_url,
                "title": title,
                "blog": {"id": blog_id},
                "status": "LIVE",
            }
            return BloggerPublishResult(
                post_id=self.post_id,
                destination_url=self.destination_url,
                raw_response=raw_response,
            )
        elif self.mode == "timeout":
            raise BloggerTransportTimeoutError("Blogger transport timed out waiting for response")
        elif self.mode == "disconnect":
            raise BloggerTransportTimeoutError("Connection closed unexpectedly by Blogger remote peer")
        elif self.mode in ("auth_failure", "bad_request", "error"):
            status = 401 if self.mode == "auth_failure" else self.error_status
            msg = "Unauthorized" if self.mode == "auth_failure" else self.error_message
            raise BloggerAuthoritativeError(status, msg, {"mode": self.mode})
        else:
            raise ValueError(f"Unknown ControlledBloggerAdapter mode: {self.mode}")


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
    ) -> tuple[dict[str, Any], Path, str]:
        """Perform All-or-Nothing preflight checks before any delivery attempt.

        Returns (auth_record, canonical_artifact_path, content_hash).
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

        artifact_id = active_auth["artifact_id"]
        expected_hash = active_auth["artifact_content_hash"]

        # 1. 5 cuts current check (Gate 1: Currency)
        cuts = snap.get("cuts", [])
        if len(cuts) != 5:
            raise ReleasePreflightError(f"Expected exactly 5 cuts, found {len(cuts)}")
        for cut in cuts:
            cid = cut["cut_id"]
            if cut.get("desired_revision") is None or cut.get("realized_revision") != cut.get("desired_revision"):
                raise RealizationIncompleteError(f"Cut {cid} is not current (STALE)")

        # 2. Artifact cut closure check
        art_path = self.store.project_dir / "assets" / "review-artifacts" / f"{artifact_id}.png"
        if not art_path.is_file():
            raise SourceAssetMissingError(f"Review artifact file missing at {art_path}")

        # Hash check of review artifact
        actual_art_bytes = art_path.read_bytes()
        actual_art_hash = hashlib.sha256(actual_art_bytes).hexdigest()
        if actual_art_hash != expected_hash:
            raise SourceAssetMissingError(
                f"Review artifact hash corrupted: expected {expected_hash}, got {actual_art_hash}"
            )

        # Dimension / format verification with Pillow
        try:
            with Image.open(art_path) as im:
                if im.size != (CANONICAL_WIDTH, CANONICAL_HEIGHT):
                    raise SourceAssetMissingError(
                        f"Review artifact dimensions {im.size} != expected ({CANONICAL_WIDTH}, {CANONICAL_HEIGHT})"
                    )
                if im.format != "PNG":
                    raise SourceAssetMissingError(f"Review artifact format {im.format} != PNG")
        except Exception as exc:
            if isinstance(exc, SourceAssetMissingError):
                raise
            raise SourceAssetMissingError(f"Failed to read review artifact image: {exc}") from exc

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

        return active_auth, art_path, expected_hash

    def export_png(
        self,
        expected_authority_revision: int,
        output_path: Path | str | None = None,
        authorization_id: str | None = None,
        attempt_id: str | None = None,
    ) -> DeliveryResult:
        """Export canonical PNG without reflow, copying bytes atomically and reading back hash."""
        active_auth, art_path, expected_hash = self.preflight_release(authorization_id)
        auth_id = active_auth["authorization_id"]
        art_id = active_auth["artifact_id"]

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
            # 2. CFW-2 Atomic byte export: write to temporary file in same directory then os.replace
            temp_fd, temp_file_str = tempfile.mkstemp(
                prefix=".tmp-export-",
                dir=str(dest_path.parent),
                suffix=".png",
            )
            os.close(temp_fd)
            temp_path = Path(temp_file_str)

            try:
                # Direct stream copy of canonical review artifact
                shutil.copyfile(art_path, temp_path)
                os.replace(temp_path, dest_path)
            finally:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

            # 3. Readback verification
            exported_bytes = dest_path.read_bytes()
            exported_hash = hashlib.sha256(exported_bytes).hexdigest()
            if exported_hash != expected_hash:
                raise DeliveryError(
                    f"Readback hash mismatch: exported {exported_hash} != artifact {expected_hash}"
                )

            with Image.open(dest_path) as im:
                if im.size != (CANONICAL_WIDTH, CANONICAL_HEIGHT):
                    raise DeliveryError(f"Exported image dimension mismatch: {im.size}")
                if im.format != "PNG":
                    raise DeliveryError(f"Exported image format mismatch: {im.format}")

            evidence = {
                "sha256": exported_hash,
                "bytes_written": len(exported_bytes),
                "width": CANONICAL_WIDTH,
                "height": CANONICAL_HEIGHT,
                "output_path": str(dest_path),
            }

            # 4. Record delivery observation in separate transaction
            # In case authority changed between start and record, refresh revision
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
    ) -> DeliveryResult:
        """Deliver comic to Blogger: start (unknown) -> external I/O -> record observation."""
        active_auth, art_path, expected_hash = self.preflight_release(authorization_id)
        auth_id = active_auth["authorization_id"]
        art_id = active_auth["artifact_id"]

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

        art_bytes = art_path.read_bytes()

        # 2. External I/O without any SQLite write lock
        publish_result: BloggerPublishResult | None = None
        transport_error: BloggerTransportTimeoutError | None = None
        auth_error: BloggerAuthoritativeError | None = None

        try:
            publish_result = effective_adapter.publish(
                effective_blog_id,
                effective_title,
                art_bytes,
                filename=f"comic-{art_id}.png",
            )
        except BloggerTransportTimeoutError as te:
            transport_error = te
        except BloggerAuthoritativeError as ae:
            auth_error = ae
        except Exception as e:
            # Treat other exceptions as authoritative/general errors
            auth_error = BloggerAuthoritativeError(500, str(e))

        # 3. Record delivery observation (transaction 2)
        if publish_result is not None:
            evidence = {
                "post_id": publish_result.post_id,
                "destination_url": publish_result.destination_url,
                "raw_response": publish_result.raw_response,
                "artifact_hash": expected_hash,
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
                bytes_written=len(art_bytes),
                evidence=evidence,
                observed_authority_revision=obs_rev,
            )

        elif transport_error is not None:
            # Honest Unknown: record stays 'unknown', evidence updated if possible or remains unknown
            # Record observation as 'unknown' with error evidence
            evidence = {
                "error": "BloggerTransportTimeoutError",
                "message": str(transport_error),
                "artifact_hash": expected_hash,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="unknown",
                evidence=evidence,
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

        else:
            assert auth_error is not None
            evidence = {
                "error": "BloggerAuthoritativeError",
                "status_code": auth_error.status_code,
                "message": auth_error.message,
                "details": auth_error.details,
            }
            obs_rev = self._record_observation_with_retry(
                start_rev,
                att_id,
                outcome="confirmed_failure",
                evidence=evidence,
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

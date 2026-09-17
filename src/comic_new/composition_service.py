"""Composition service orchestrating exact-five validation, staging, promotion, registration, and readback."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any
import uuid

from PIL import Image

from comic_new.composition import (
    CANONICAL_WIDTH,
    LEGACY_CANONICAL_HEIGHT,
    CompositionError,
    CompositionRenderError,
    CompositionValidationError,
    SHA256_HEX_RE,
    SourceAssetError,
    TypographyError,
    compute_cut_slots,
    artifact_path,
    canonical_json_dumps,
    normalize_state,
    render_canonical,
)
from comic_new.store import (
    ConflictError,
    RealizationIncompleteError,
    TransactionalStore,
)


class CompositionServiceError(CompositionError):
    """Base exception for composition service errors."""


class ArtifactReadbackError(CompositionServiceError):
    """Integrity check failed during artifact readback."""


class ArtifactNoLongerCurrentError(CompositionServiceError):
    """Registered artifact is no longer current with respect to composition or cut revisions."""
    def __init__(self, artifact_id: str, message: str | None = None) -> None:
        super().__init__(message or f"Artifact {artifact_id} is no longer current")
        self.artifact_id = artifact_id


@dataclass(frozen=True)
class MaterializedArtifact:
    artifact_id: str
    content_hash: str
    path: Path
    width: int
    height: int
    composition_revision: int
    closure: list[dict[str, Any]]
    bytes_data: bytes


class CompositionService:
    """Orchestrates canonical review artifact materialization and verified readback."""

    def __init__(self, store: TransactionalStore, font_path: Path | str) -> None:
        self.store = store
        self.font_path = Path(font_path)
        if not self.font_path.is_file():
            raise TypographyError(f"Font file does not exist at {self.font_path}")
        self._font_bytes = self.font_path.read_bytes()
        self._font_sha256 = hashlib.sha256(self._font_bytes).hexdigest()

    @property
    def project_dir(self) -> Path:
        return self.store.project_dir

    def materialize(
        self,
        expected_authority_revision: int,
        expected_composition_revision: int,
    ) -> MaterializedArtifact:
        """Materialize canonical review artifact from current snapshot.
        
        Orchestration order:
        1. Authoritative capture (snapshot)
        2. Preflight all inputs (cuts exact-five, current, valid PNG decode)
        3. Render staging (.composition-staging/<random>/candidate.png)
        4. Validate candidate (decode, dimensions, hash, metadata)
        5. No-overwrite promote to assets/review-artifacts/<artifact_id>.png
        6. Register in store via existing register_review_artifact
        7. Authoritative fresh readback
        """
        snap = self.store.snapshot()
        actual_auth_rev = snap["authority_revision"]
        if actual_auth_rev != expected_authority_revision:
            raise ConflictError(
                expected=expected_authority_revision,
                actual=actual_auth_rev,
                message=f"Authority revision mismatch: expected {expected_authority_revision}, actual is {actual_auth_rev}",
            )

        comp_dict = snap.get("composition") or {}
        actual_comp_rev = comp_dict.get("revision")
        if actual_comp_rev != expected_composition_revision:
            raise ConflictError(
                expected=expected_composition_revision,
                actual=actual_comp_rev,
                message=f"Composition revision mismatch: expected {expected_composition_revision}, actual is {actual_comp_rev}",
            )

        raw_state = comp_dict.get("state")
        if not isinstance(raw_state, dict):
            try:
                raw_state = json.loads(comp_dict.get("state_json") or "{}")
            except Exception as e:
                raise CompositionValidationError(f"Invalid composition state_json: {e}") from e

        norm_state = normalize_state(raw_state)
        snap_cuts = snap.get("cuts", [])

        if not isinstance(snap_cuts, list) or not snap_cuts:
            raise RealizationIncompleteError("Active cut set is empty")
        ordered_cut_ids = [cut["cut_id"] for cut in snap_cuts]
        if len(norm_state["slot_heights_px"]) != len(snap_cuts):
            raise CompositionRenderError(
                f"Composition slot count {len(norm_state['slot_heights_px'])} does not match cuts {len(snap_cuts)}"
            )

        # Check all cuts are current before materialization.
        real_complete = snap.get("realization_complete", {})
        if not real_complete.get("complete", False):
            raise RealizationIncompleteError("Realization is incomplete: not all active cuts are current")
        # Prepare cuts payload with source bytes read and preflight
        cuts_payload: list[dict[str, Any]] = []
        for c in snap_cuts:
            cid = c["cut_id"]
            d_rev = c.get("desired_revision")
            r_rev = c.get("realized_revision")
            if d_rev is None or r_rev != d_rev:
                raise RealizationIncompleteError(f"Cut {cid} is not current (desired={d_rev}, realized={r_rev})")

            asset_path_rel = c.get("realized_asset_path")
            expected_hash = c.get("realized_content_hash")
            asset_id = c.get("realized_asset_id")

            if not asset_path_rel or not expected_hash or not asset_id:
                raise RealizationIncompleteError(f"Cut {cid} realization metadata missing: path={asset_path_rel}, hash={expected_hash}, asset_id={asset_id}")

            abs_asset_path = self.project_dir / asset_path_rel
            if not abs_asset_path.is_file():
                raise SourceAssetError(f"Cut {cid} realization file missing at {abs_asset_path}")

            source_bytes = abs_asset_path.read_bytes()
            actual_src_hash = hashlib.sha256(source_bytes).hexdigest()
            if actual_src_hash != expected_hash:
                raise SourceAssetError(f"Cut {cid} hash mismatch: DB has {expected_hash}, file has {actual_src_hash}")

            # Verify decodable PNG
            try:
                src_img = Image.open(io.BytesIO(source_bytes))
                src_img.load()
                if src_img.format != "PNG":
                    raise SourceAssetError(f"Cut {cid} format is {src_img.format}, expected PNG")
            except Exception as e:
                if isinstance(e, SourceAssetError):
                    raise
                raise SourceAssetError(f"Cut {cid} failed to decode: {e}") from e

            cuts_payload.append({
                "cut_id": cid,
                "desired_revision": d_rev,
                "realized_revision": r_rev,
                "realized_asset_id": asset_id,
                "realized_content_hash": expected_hash,
                "source_bytes": source_bytes,
            })

        # Render canonical in-memory
        rendered = render_canonical(
            state=norm_state,
            composition_revision=actual_comp_rev,
            cuts=cuts_payload,
            font_bytes=self._font_bytes,
            ordered_cut_ids=ordered_cut_ids,
        )

        # Set up staging directory
        staging_root = self.project_dir / ".composition-staging"
        staging_dir = staging_root / str(uuid.uuid4())
        staging_dir.mkdir(parents=True, exist_ok=True)
        staging_file = staging_dir / "candidate.png"

        final_dest = artifact_path(self.project_dir, rendered.artifact_id)
        final_dest.parent.mkdir(parents=True, exist_ok=True)


        try:
            # Write staging file
            staging_file.write_bytes(rendered.png_bytes)

            # Validate staging file from disk
            read_staging_bytes = staging_file.read_bytes()
            read_staging_hash = hashlib.sha256(read_staging_bytes).hexdigest()
            if read_staging_hash != rendered.content_hash:
                raise CompositionRenderError("Staging file hash mismatch with in-memory render")

            stg_img = Image.open(io.BytesIO(read_staging_bytes))
            stg_img.load()
            if stg_img.format != "PNG" or stg_img.size != (rendered.width, rendered.height):
                raise CompositionRenderError(f"Staging image invalid format/size: {stg_img.format}, {stg_img.size}")
            stg_closure = stg_img.text.get("comic_new_closure")
            if not stg_closure or stg_closure != rendered.metadata_json:
                raise CompositionRenderError("Staging image metadata mismatch")

            # 5. Exclusive no-overwrite publish via direct os.link (no replace/copy fallback)
            try:
                os.link(staging_file, final_dest)
            except FileExistsError:
                pass
            except Exception as link_err:
                raise CompositionRenderError(f"Failed to publish artifact to {final_dest} via hardlink: {link_err}") from link_err

            # Validate final_dest bytes, hash, and full decode
            final_bytes = final_dest.read_bytes()
            final_hash = hashlib.sha256(final_bytes).hexdigest()
            if final_hash != rendered.content_hash:
                raise CompositionRenderError(f"Existing file at {final_dest} has mismatched hash: {final_hash} vs {rendered.content_hash}")

            fin_img = Image.open(io.BytesIO(final_bytes))
            fin_img.load()
            if fin_img.format != "PNG" or fin_img.size != (rendered.width, rendered.height):
                raise CompositionRenderError(f"Final image invalid format/size: {fin_img.format}, {fin_img.size}")
            fin_closure = fin_img.text.get("comic_new_closure")
            if not fin_closure or fin_closure != rendered.metadata_json:
                raise CompositionRenderError("Final image metadata mismatch")

            # Clean private staging file and dir
            if staging_file.exists():
                staging_file.unlink(missing_ok=True)
            if staging_dir.exists():
                try:
                    staging_dir.rmdir()
                except OSError:
                    pass

            # 6. Register in store via existing register_review_artifact
            registration_closure = [
                {
                    "cut_id": item["cut_id"],
                    "display_order": item["display_order"],
                    "realized_revision": item["realized_revision"],
                    "asset_id": item["asset_id"],
                }
                for item in rendered.closure
            ]

            try:
                self.store.register_review_artifact(
                    expected_authority_revision=actual_auth_rev,
                    artifact_id=rendered.artifact_id,
                    content_hash=rendered.content_hash,
                    composition_revision=actual_comp_rev,
                    cut_closure=registration_closure,
                )
            except Exception as reg_err:
                # 7. Registration outcome / strict duplicate convergence
                # Note: NEVER unlink final_dest under any registration failure!
                # Query fresh snapshot
                fresh_snap = self.store.snapshot()
                reg_artifacts = {a["artifact_id"]: a for a in fresh_snap.get("review_artifacts", [])}
                if rendered.artifact_id not in reg_artifacts:
                    raise reg_err

                # Assert fresh snapshot sequence-current before accepting pre-existing artifact
                self._assert_snapshot_sequence_current(fresh_snap, rendered.artifact_id)
                # Strict 7-step comparison for duplicate convergence:
                art_row = reg_artifacts[rendered.artifact_id]
                # 1) Row fields: artifact_id, content_hash, composition_revision
                if (
                    art_row.get("content_hash") != rendered.content_hash
                    or art_row.get("composition_revision") != actual_comp_rev
                ):
                    raise reg_err

                # Compare the complete ordered active closure, not just its length.
                db_cuts = art_row.get("cuts", [])
                if len(db_cuts) != len(rendered.closure) or [c.get("cut_id") for c in db_cuts] != [c["cut_id"] for c in rendered.closure]:
                    raise reg_err
                for idx, c_item in enumerate(rendered.closure):
                    db_c = db_cuts[idx]
                    if (
                        db_c.get("cut_id") != c_item["cut_id"]
                        or db_c.get("realized_revision") != c_item["realized_revision"]
                        or db_c.get("asset_id") != c_item["asset_id"]
                    ):
                        raise reg_err

                # 3) Embedded closure metadata in final file
                if fin_closure != rendered.metadata_json:
                    raise reg_err

                # 4) Actual bytes and hash of final file
                if final_hash != rendered.content_hash:
                    raise reg_err

                # 5) Current composition revision in snapshot
                cur_comp = (fresh_snap.get("composition") or {}).get("revision")
                if cur_comp != actual_comp_rev:
                    raise ArtifactNoLongerCurrentError(
                        rendered.artifact_id,
                        f"Composition revision changed to {cur_comp} during race",
                    )

                # Current snapshot must retain the same ordered active IDs.
                fresh_cuts = fresh_snap.get("cuts", [])
                if len(fresh_cuts) != len(rendered.closure) or [c.get("cut_id") for c in fresh_cuts] != [c["cut_id"] for c in rendered.closure]:
                    raise ArtifactNoLongerCurrentError(rendered.artifact_id, "Snapshot active cuts changed")
                for idx, c_item in enumerate(rendered.closure):
                    fc = fresh_cuts[idx]
                    if (
                        fc.get("cut_id") != c_item["cut_id"]
                        or fc.get("desired_revision") != c_item["desired_revision"]
                        or fc.get("realized_revision") != c_item["realized_revision"]
                        or fc.get("realized_asset_id") != c_item["asset_id"]
                    ):
                        raise ArtifactNoLongerCurrentError(
                            rendered.artifact_id,
                            f"Cut {c_item['cut_id']} realization identity changed during race",
                        )

            # 8. Authoritative fresh readback
            return self._verify_and_build_artifact(
                rendered.artifact_id,
                expected_comp_rev=actual_comp_rev,
                expected_closure=rendered.closure,
            )

        except Exception:
            # Cleanup staging in all failure cases
            if staging_file.exists():
                staging_file.unlink(missing_ok=True)
            if staging_dir.exists():
                try:
                    staging_dir.rmdir()
                except OSError:
                    pass
            raise

    def read_artifact(self, artifact_id: str) -> MaterializedArtifact:
        """Read and verify artifact by artifact_id.
        
        Verifies DB registration, file existence, content hash, image format/dimensions,
        and embedded metadata.
        """
        return self._verify_and_build_artifact(artifact_id)

    def _assert_snapshot_sequence_current(self, snapshot: dict[str, Any], artifact_id: str) -> None:
        """Assert that a snapshot remains current for its ordered active cuts."""
        realization_complete = snapshot.get("realization_complete") or {}
        if realization_complete.get("complete") is not True:
            raise ArtifactNoLongerCurrentError(
                artifact_id,
                f"Artifact {artifact_id} realization is incomplete in snapshot (status: {realization_complete.get('status')})",
            )
        cuts = snapshot.get("cuts", [])
        cut_ids = [cut.get("cut_id") for cut in cuts]
        if not cuts or len(set(cut_ids)) != len(cut_ids) or any(not isinstance(cid, int) or cid < 1 for cid in cut_ids):
            raise ArtifactNoLongerCurrentError(artifact_id, f"Artifact {artifact_id} snapshot active cuts are invalid")
        for cut in cuts:
            cid = cut.get("cut_id")
            if cut.get("currency") != "CURRENT":
                raise ArtifactNoLongerCurrentError(
                    artifact_id,
                    f"Artifact {artifact_id} cut {cid} currency is {cut.get('currency')}, expected CURRENT",
                )

    def _verify_and_build_artifact(
        self,
        artifact_id: str,
        expected_comp_rev: int | None = None,
        expected_closure: list[dict[str, Any]] | None = None,
    ) -> MaterializedArtifact:
        # 1. Query DB snapshot first (authoritative DB-first reader)
        snap = self.store.snapshot()
        reg_artifacts = {a["artifact_id"]: a for a in snap.get("review_artifacts", [])}
        if artifact_id not in reg_artifacts:
            raise ArtifactReadbackError(f"Artifact {artifact_id} is not registered in store")

        art_row = reg_artifacts[artifact_id]
        expected_hash = art_row["content_hash"]
        comp_rev = art_row["composition_revision"]
        art_closure = art_row.get("cuts", [])

        if artifact_id != f"artifact-{expected_hash}":
            raise ArtifactReadbackError(f"artifact_id {artifact_id} does not match artifact-{expected_hash}")

        closure_ids = [c.get("cut_id") for c in art_closure]
        if not closure_ids or len(set(closure_ids)) != len(closure_ids) or any(not isinstance(cid, int) or cid < 1 for cid in closure_ids):
            raise ArtifactReadbackError(f"Artifact {artifact_id} closure IDs are invalid")
        if [c.get("display_order") for c in art_closure] != list(range(1, len(art_closure) + 1)):
            raise ArtifactReadbackError(f"Artifact {artifact_id} closure display order is invalid")

        # 2. Check currentness against current snapshot if requested
        if expected_comp_rev is not None or expected_closure is not None:
            self._assert_snapshot_sequence_current(snap, artifact_id)

        if expected_comp_rev is not None:
            cur_comp_rev = (snap.get("composition") or {}).get("revision")
            if cur_comp_rev != expected_comp_rev or comp_rev != cur_comp_rev:
                raise ArtifactNoLongerCurrentError(
                    artifact_id,
                    f"Artifact {artifact_id} composition revision {comp_rev} is not current (current is {cur_comp_rev})",
                )

        if expected_closure is not None:
            current_cuts = snap.get("cuts", [])
            if [c.get("cut_id") for c in current_cuts] != [c["cut_id"] for c in expected_closure]:
                raise ArtifactNoLongerCurrentError(artifact_id, "Snapshot active cut order changed")
            for idx, exp_c in enumerate(expected_closure):
                cc = current_cuts[idx]
                cid = exp_c["cut_id"]
                exp_d_rev = exp_c.get("desired_revision", exp_c.get("realized_revision"))
                if (
                    cc.get("cut_id") != cid
                    or cc.get("desired_revision") != exp_d_rev
                    or cc.get("realized_revision") != exp_c.get("realized_revision")
                    or cc.get("realized_asset_id") != exp_c.get("asset_id")
                ):
                    raise ArtifactNoLongerCurrentError(
                        artifact_id,
                        f"Cut {cid} identity no longer current in snapshot",
                    )

        # 3. Read file from assets/review-artifacts/<artifact_id>.png
        dest_path = artifact_path(self.project_dir, artifact_id)
        if not dest_path.is_file():
            raise ArtifactReadbackError(f"Artifact file missing at {dest_path}")

        file_bytes = dest_path.read_bytes()
        actual_hash = hashlib.sha256(file_bytes).hexdigest()
        if actual_hash != expected_hash:
            raise ArtifactReadbackError(f"Artifact file hash mismatch: DB has {expected_hash}, file has {actual_hash}")

        # 4. Full image decode and dimensions check
        try:
            img = Image.open(io.BytesIO(file_bytes))
            img.load()
            if img.format != "PNG":
                raise ArtifactReadbackError(f"Artifact image is not PNG, got {img.format}")
            if img.mode != "RGB":
                raise ArtifactReadbackError(f"Artifact image mode is {img.mode}, expected RGB")
            closure_raw = img.text.get("comic_new_closure")
            if not closure_raw:
                raise ArtifactReadbackError("Artifact missing comic_new_closure metadata")
            meta = json.loads(closure_raw)
            contract = meta.get("contract")
            if contract == "canonical-composition/v1":
                expected_width, expected_height = CANONICAL_WIDTH, LEGACY_CANONICAL_HEIGHT
                if img.size != (expected_width, expected_height):
                    raise ArtifactReadbackError(f"Legacy artifact size {img.size} != {(expected_width, expected_height)}")
                if not isinstance(meta.get("state"), dict) or not isinstance(meta.get("font_sha256"), str):
                    raise ArtifactReadbackError("Legacy artifact metadata is incomplete")
            elif contract == "canonical-composition/v2":
                meta_state = meta.get("state")
                if not isinstance(meta_state, dict):
                    raise ArtifactReadbackError("Metadata state is not dict")
                normalized_meta_state = normalize_state(meta_state)
                slots = compute_cut_slots(normalized_meta_state["slot_heights_px"], normalized_meta_state["gap_px"], closure_ids)
                expected_width = normalized_meta_state["canvas_width_px"]
                expected_height = slots[-1].bottom_px
                if img.size != (expected_width, expected_height):
                    raise ArtifactReadbackError(f"Artifact size {img.size} != {(expected_width, expected_height)}")
                if meta.get("width_px") != expected_width or meta.get("height_px") != expected_height:
                    raise ArtifactReadbackError("Dimensions in metadata mismatch")
                if meta.get("gap_px") != normalized_meta_state["gap_px"] or meta.get("fit") != "contain":
                    raise ArtifactReadbackError("Geometry fit metadata mismatch")
                if meta.get("slots") != [slot.__dict__ for slot in slots]:
                    raise ArtifactReadbackError("Resolved slot metadata mismatch")
                if meta.get("font_sha256") != normalized_meta_state["font_sha256"]:
                    raise ArtifactReadbackError(
                        f"Metadata font_sha256 {meta.get('font_sha256')} != embedded state {normalized_meta_state['font_sha256']}"
                    )
            else:
                raise ArtifactReadbackError(f"Invalid contract in metadata: {contract}")
            if meta.get("composition_revision") != comp_rev:
                raise ArtifactReadbackError(f"Metadata comp_rev {meta.get('composition_revision')} != DB {comp_rev}")
            # Validate embedded cuts closure matches DB cuts.
            meta_cuts = meta.get("cuts", [])
            if [c.get("cut_id") for c in meta_cuts] != [c.get("cut_id") for c in art_closure]:
                raise ArtifactReadbackError(f"Artifact {artifact_id} embedded cut order mismatch")
            for idx, mc in enumerate(meta_cuts):
                db_c = art_closure[idx]
                cid = mc.get("cut_id")
                metadata_order = mc.get("display_order")
                if metadata_order is not None and (metadata_order != db_c.get("display_order") or metadata_order != idx + 1):
                    raise ArtifactReadbackError(f"Cut {cid} display order mismatch")
                if mc.get("realized_revision") != db_c.get("realized_revision"):
                    raise ArtifactReadbackError(f"Cut {cid} revision mismatch")
                if mc.get("asset_id") != db_c.get("asset_id"):
                    raise ArtifactReadbackError(f"Cut {cid} asset_id mismatch")
                if mc.get("desired_revision") != mc.get("realized_revision"):
                    raise ArtifactReadbackError(f"Cut {cid} meta desired_rev != realized_rev")
                src_hash = mc.get("source_content_hash")
                if not isinstance(src_hash, str) or not SHA256_HEX_RE.match(src_hash):
                    raise ArtifactReadbackError(f"Cut {cid} meta source_content_hash invalid: {src_hash}")

        except Exception as e:
            if isinstance(e, (ArtifactReadbackError, ArtifactNoLongerCurrentError)):
                raise
            raise ArtifactReadbackError(f"Failed to decode or verify artifact: {e}") from e

        return MaterializedArtifact(
            artifact_id=artifact_id,
            content_hash=actual_hash,
            path=dest_path,
            width=expected_width,
            height=expected_height,
            composition_revision=comp_rev,
            closure=art_closure,
            bytes_data=file_bytes,
        )

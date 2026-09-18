"""Canonical composition, geometry, PIL rendering, and deterministic PNG encoding."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Sequence

from PIL import Image, ImageColor, ImageDraw, ImageFont, PngImagePlugin
import PIL

CANONICAL_WIDTH = 1024
# Legacy v1's fixed surface is retained only for data migration. Runtime height
# is derived from the accepted integer slot heights in composition state.
LEGACY_CANONICAL_HEIGHT = 7680
CANONICAL_HEIGHT = LEGACY_CANONICAL_HEIGHT
SCHEMA_VERSION = 2
RENDERER_CONTRACT = "canonical-composition/v2"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{8}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ResolvedSlot:
    cut_id: int
    top_px: int
    bottom_px: int
    height_px: int


class CompositionError(Exception):
    """Base exception for composition domain."""


class CompositionValidationError(CompositionError):
    """Validation failed for composition state."""


class CompositionRenderError(CompositionError):
    """Rendering failed (e.g. text overflow, missing/corrupt cut)."""


class SourceAssetError(CompositionRenderError):
    """Cut source image is missing, corrupt, or unreadable."""


class TypographyError(CompositionRenderError):
    """Font missing, hash mismatch, or text overflow."""


@dataclass(frozen=True)
class RenderedArtifactBytes:
    png_bytes: bytes
    content_hash: str
    artifact_id: str
    width: int
    height: int
    composition_revision: int
    closure: list[dict[str, Any]]
    metadata_json: str


def _round_half_up(val: Decimal) -> int:
    return int(val.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_half_up(val: Decimal | float | int | str) -> int:
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return _round_half_up(val)


def normalize_percentage(val: Any, field_name: str, *, min_val: Decimal = Decimal("0"), max_val: Decimal = Decimal("100"), strictly_greater_than_min: bool = False, strictly_less_than_max: bool = False) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise CompositionValidationError(f"Field {field_name} must be a JSON number, got {val!r}")
    try:
        d = Decimal(str(val))
    except Exception as e:
        raise CompositionValidationError(f"Field {field_name} must be a valid decimal number: {e}") from e
    if not d.is_finite():
        raise CompositionValidationError(f"Field {field_name} must be finite")

    d_norm = d.normalize()
    if d_norm.as_tuple().exponent < -4:
        raise CompositionValidationError(f"Field {field_name} exceeds 4 decimal places: {val}")

    if strictly_greater_than_min:
        if d <= min_val:
            raise CompositionValidationError(f"Field {field_name} must be > {min_val}, got {d}")
    else:
        if d < min_val:
            raise CompositionValidationError(f"Field {field_name} must be >= {min_val}, got {d}")

    if strictly_less_than_max:
        if d >= max_val:
            raise CompositionValidationError(f"Field {field_name} must be < {max_val}, got {d}")
    else:
        if d > max_val:
            raise CompositionValidationError(f"Field {field_name} must be <= {max_val}, got {d}")

    return float(d)


def normalize_legacy_coordinate(val: Any, field_name: str) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise CompositionValidationError(f"Field {field_name} must be a JSON number, got {val!r}")
    try:
        d = Decimal(str(val))
    except Exception as exc:
        raise CompositionValidationError(f"Field {field_name} must be a valid decimal number: {exc}") from exc
    if not d.is_finite() or d.normalize().as_tuple().exponent < -4:
        raise CompositionValidationError(f"Field {field_name} must be a finite number with at most 4 decimal places")
    return float(d)


def normalize_color(val: Any, field_name: str) -> str:
    if not isinstance(val, str) or not HEX_COLOR_RE.match(val):
        raise CompositionValidationError(f"Field {field_name} must be #RRGGBBAA hex string, got {val!r}")
    return val.upper()


def _normalize_ordered_cut_ids(
    ordered_cut_ids: Sequence[int] | None,
    slot_count: int,
) -> list[int] | None:
    """Validate stable active cut identities against the ordered slot count."""
    if ordered_cut_ids is None:
        return None
    if isinstance(ordered_cut_ids, (str, bytes, bytearray)) or not isinstance(ordered_cut_ids, Sequence):
        raise CompositionValidationError("ordered_cut_ids must be a sequence")
    ids = list(ordered_cut_ids)
    if (
        len(ids) != slot_count
        or not ids
        or any(isinstance(cid, bool) or not isinstance(cid, int) or cid < 1 for cid in ids)
        or len(set(ids)) != len(ids)
    ):
        raise CompositionValidationError("ordered_cut_ids must be unique positive IDs matching slot heights")
    return ids


def _normalize_bubble_style(b: dict[str, Any], idx: int) -> dict[str, Any]:
    """Validate and normalize fields shared by anchored and legacy bubbles."""
    bubble_id = b.get("bubble_id")
    if not isinstance(bubble_id, str) or not bubble_id.strip():
        raise CompositionValidationError(f"bubble_id at index {idx} must be non-empty string")
    cut_id = b.get("cut_id")
    if isinstance(cut_id, bool) or not isinstance(cut_id, int) or cut_id < 1:
        raise CompositionValidationError(f"cut_id at index {idx} must be a positive integer, got {cut_id!r}")
    shape = b.get("shape")
    if shape not in ("ellipse", "rounded_rectangle"):
        raise CompositionValidationError(f"shape at index {idx} must be 'ellipse' or 'rounded_rectangle', got {shape!r}")
    text = b.get("text")
    if not isinstance(text, str):
        raise CompositionValidationError(f"bubbles[{idx}].text must be string, got {type(text)}")
    font_size_pct = normalize_percentage(
        b.get("font_size_pct"), f"bubbles[{idx}].font_size_pct",
        min_val=Decimal("0"), max_val=Decimal("100"), strictly_greater_than_min=True,
    )
    line_spacing_pct = normalize_percentage(
        b.get("line_spacing_pct"), f"bubbles[{idx}].line_spacing_pct",
        min_val=Decimal("0"), max_val=Decimal("500"),
    )
    text_align = b.get("text_align")
    if text_align not in ("left", "center", "right"):
        raise CompositionValidationError(f"bubbles[{idx}].text_align must be 'left', 'center', or 'right', got {text_align!r}")
    text_rgba = normalize_color(b.get("text_rgba"), f"bubbles[{idx}].text_rgba")
    fill_rgba = normalize_color(b.get("fill_rgba"), f"bubbles[{idx}].fill_rgba")
    outline_rgba = normalize_color(b.get("outline_rgba"), f"bubbles[{idx}].outline_rgba")
    outline_width_pct = normalize_percentage(
        b.get("outline_width_pct"), f"bubbles[{idx}].outline_width_pct",
        min_val=Decimal("0"), max_val=Decimal("20"),
    )
    padding_pct = normalize_percentage(
        b.get("padding_pct"), f"bubbles[{idx}].padding_pct",
        min_val=Decimal("0"), max_val=Decimal("50"), strictly_less_than_max=True,
    )
    return {
        "bubble_id": bubble_id,
        "cut_id": cut_id,
        "shape": shape,
        "text": text,
        "font_size_pct": font_size_pct,
        "line_spacing_pct": line_spacing_pct,
        "text_align": text_align,
        "text_rgba": text_rgba,
        "fill_rgba": fill_rgba,
        "outline_rgba": outline_rgba,
        "outline_width_pct": outline_width_pct,
        "padding_pct": padding_pct,
    }


def normalize_state(
    state: dict[str, Any],
    ordered_cut_ids: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Normalize composition state into the strict canonical schema v2.

    v1/global bubbles are accepted only by the store's one-shot migration. The
    runtime/API path is deliberately v2-only so there is no dual authority.
    When the authoritative ordered active cut IDs are available, bubble owners
    are validated by stable membership rather than by comparing ID magnitude
    with the number of slots.
    """
    if not isinstance(state, dict):
        raise CompositionValidationError(f"Composition state must be a dict, got {type(state)}")
    allowed_top_keys = {
        "schema_version", "canvas_width_px", "gap_px", "slot_heights_px",
        "fit", "font_sha256", "bubbles",
    }
    unknown_top = set(state.keys()) - allowed_top_keys
    if unknown_top:
        raise CompositionValidationError(f"Unknown top-level keys in state: {sorted(unknown_top)}")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise CompositionValidationError(f"schema_version must be {SCHEMA_VERSION}, got {state.get('schema_version')!r}")
    width = state.get("canvas_width_px")
    if isinstance(width, bool) or not isinstance(width, int) or width != CANONICAL_WIDTH:
        raise CompositionValidationError(f"canvas_width_px must be {CANONICAL_WIDTH}, got {width!r}")
    gap_px = state.get("gap_px")
    if isinstance(gap_px, bool) or not isinstance(gap_px, int) or gap_px < 0:
        raise CompositionValidationError(f"gap_px must be a non-negative integer, got {gap_px!r}")
    heights = state.get("slot_heights_px")
    if not isinstance(heights, list) or not heights:
        raise CompositionValidationError("slot_heights_px must be a non-empty list")
    normalized_heights: list[int] = []
    for idx, height in enumerate(heights):
        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            raise CompositionValidationError(f"slot_heights_px[{idx}] must be a positive integer, got {height!r}")
        normalized_heights.append(height)
    normalized_cut_ids = _normalize_ordered_cut_ids(ordered_cut_ids, len(normalized_heights))
    active_cut_ids = set(normalized_cut_ids) if normalized_cut_ids is not None else None
    if state.get("fit") != "contain":
        raise CompositionValidationError(f"fit must be 'contain', got {state.get('fit')!r}")
    font_sha256 = state.get("font_sha256")
    if not isinstance(font_sha256, str) or not SHA256_HEX_RE.match(font_sha256):
        raise CompositionValidationError(f"font_sha256 must be 64-character lowercase hex sha256, got {font_sha256!r}")
    bubbles_raw = state.get("bubbles")
    if not isinstance(bubbles_raw, list):
        raise CompositionValidationError(f"bubbles must be a list, got {type(bubbles_raw)}")

    normalized_bubbles: list[dict[str, Any]] = []
    seen_bubble_ids: set[str] = set()
    anchored_keys = {
        "anchor_status", "bubble_id", "cut_id", "shape", "local_x_pct", "local_y_pct",
        "local_w_pct", "local_h_pct", "text", "font_size_pct", "line_spacing_pct",
        "text_align", "text_rgba", "fill_rgba", "outline_rgba", "outline_width_pct", "padding_pct",
    }
    reanchor_keys = {
        "anchor_status", "bubble_id", "cut_id", "shape", "legacy_global_rect", "text",
        "font_size_pct", "line_spacing_pct", "text_align", "text_rgba", "fill_rgba",
        "outline_rgba", "outline_width_pct", "padding_pct",
    }
    for idx, raw in enumerate(bubbles_raw):
        if not isinstance(raw, dict):
            raise CompositionValidationError(f"Bubble at index {idx} must be a dict")
        status = raw.get("anchor_status")
        allowed = anchored_keys if status == "ANCHORED" else reanchor_keys if status == "REANCHOR_REQUIRED" else set()
        if not allowed:
            raise CompositionValidationError(f"bubbles[{idx}].anchor_status must be 'ANCHORED' or 'REANCHOR_REQUIRED'")
        unknown = set(raw.keys()) - allowed
        if unknown:
            raise CompositionValidationError(f"Unknown keys in bubble index {idx}: {sorted(unknown)}")
        style = _normalize_bubble_style(raw, idx)
        bubble_id = style["bubble_id"]
        if bubble_id in seen_bubble_ids:
            raise CompositionValidationError(f"Duplicate bubble_id {bubble_id!r} at index {idx}")
        seen_bubble_ids.add(bubble_id)
        cut_id = style["cut_id"]
        if active_cut_ids is not None and cut_id not in active_cut_ids:
            raise CompositionValidationError(
                f"cut_id at index {idx} is not in the ordered active cut set: {cut_id}"
            )
        if status == "ANCHORED":
            x_pct = normalize_percentage(raw.get("local_x_pct"), f"bubbles[{idx}].local_x_pct")
            y_pct = normalize_percentage(raw.get("local_y_pct"), f"bubbles[{idx}].local_y_pct")
            w_pct = normalize_percentage(raw.get("local_w_pct"), f"bubbles[{idx}].local_w_pct", strictly_greater_than_min=True)
            h_pct = normalize_percentage(raw.get("local_h_pct"), f"bubbles[{idx}].local_h_pct", strictly_greater_than_min=True)
            if Decimal(str(x_pct)) + Decimal(str(w_pct)) > Decimal("100"):
                raise CompositionValidationError(f"bubbles[{idx}] local_x_pct + local_w_pct exceeds 100")
            if Decimal(str(y_pct)) + Decimal(str(h_pct)) > Decimal("100"):
                raise CompositionValidationError(f"bubbles[{idx}] local_y_pct + local_h_pct exceeds 100")
            normalized_bubbles.append({
                "anchor_status": "ANCHORED", **style,
                "local_x_pct": x_pct, "local_y_pct": y_pct,
                "local_w_pct": w_pct, "local_h_pct": h_pct,
            })
        else:
            legacy = raw.get("legacy_global_rect")
            if not isinstance(legacy, dict) or set(legacy) != {"x_pct", "y_pct", "w_pct", "h_pct"}:
                raise CompositionValidationError(f"bubbles[{idx}].legacy_global_rect must contain x_pct/y_pct/w_pct/h_pct")
            legacy_norm = {
                key: normalize_legacy_coordinate(legacy.get(key), f"bubbles[{idx}].legacy_global_rect.{key}")
                for key in ("x_pct", "y_pct", "w_pct", "h_pct")
            }
            normalized_bubbles.append({
                "anchor_status": "REANCHOR_REQUIRED", **style,
                "legacy_global_rect": legacy_norm,
            })

    return {
        "schema_version": SCHEMA_VERSION,
        "canvas_width_px": CANONICAL_WIDTH,
        "gap_px": gap_px,
        "slot_heights_px": normalized_heights,
        "fit": "contain",
        "font_sha256": font_sha256,
        "bubbles": normalized_bubbles,
    }


def canonical_json_dumps(obj: Any) -> str:
    """Deterministic, compact canonical JSON serialization."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_cut_slots(
    slot_heights_px: Sequence[int],
    gap_px: int,
    ordered_cut_ids: Sequence[int] | None = None,
) -> list[ResolvedSlot]:
    """Resolve ordered positive heights and stable cut IDs into integer bounds."""
    if isinstance(slot_heights_px, (str, bytes, bytearray)) or not isinstance(slot_heights_px, Sequence) or not slot_heights_px:
        raise CompositionValidationError("slot_heights_px must be a non-empty sequence")
    if isinstance(gap_px, bool) or not isinstance(gap_px, int) or gap_px < 0:
        raise CompositionValidationError(f"gap_px must be a non-negative integer, got {gap_px!r}")
    ids = _normalize_ordered_cut_ids(ordered_cut_ids, len(slot_heights_px))
    if ids is None:
        ids = list(range(1, len(slot_heights_px) + 1))
    slots: list[ResolvedSlot] = []
    cursor = 0
    for idx, height in enumerate(slot_heights_px):
        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            raise CompositionValidationError(f"slot_heights_px[{idx}] must be a positive integer, got {height!r}")
        top = cursor
        bottom = top + height
        slots.append(ResolvedSlot(ids[idx], top, bottom, height))
        cursor = bottom + (gap_px if idx < len(slot_heights_px) - 1 else 0)
    return slots


def compute_bubble_geometry(
    b: dict[str, Any], slot: ResolvedSlot | dict[str, int], canvas_width: int,
) -> tuple[int, int, int, int]:
    """Project an anchored local bubble rectangle into canvas pixel edges."""
    if b.get("anchor_status") != "ANCHORED":
        raise CompositionRenderError(f"Bubble {b.get('bubble_id')} is not anchored")
    if isinstance(canvas_width, bool) or not isinstance(canvas_width, int) or canvas_width <= 0:
        raise CompositionRenderError(f"canvas_width must be a positive integer, got {canvas_width!r}")
    try:
        if isinstance(slot, ResolvedSlot):
            slot_values = (slot.cut_id, slot.top_px, slot.bottom_px, slot.height_px)
        else:
            slot_values = (slot["cut_id"], slot["top_px"], slot["bottom_px"], slot["height_px"])
        if any(isinstance(value, bool) or not isinstance(value, int) for value in slot_values):
            raise ValueError("slot values must be integers")
        cut_id, slot_top, slot_bottom, slot_height = slot_values
    except (KeyError, TypeError, ValueError) as exc:
        raise CompositionRenderError("Invalid resolved slot") from exc
    if cut_id < 1 or slot_top < 0 or slot_height <= 0 or slot_bottom - slot_top != slot_height:
        raise CompositionRenderError(f"Invalid slot bounds for cut {cut_id}")
    if b.get("cut_id") != cut_id:
        raise CompositionRenderError(f"Bubble {b.get('bubble_id')} owner cut does not match slot {cut_id}")
    try:
        x_pct = Decimal(str(b["local_x_pct"]))
        y_pct = Decimal(str(b["local_y_pct"]))
        w_pct = Decimal(str(b["local_w_pct"]))
        h_pct = Decimal(str(b["local_h_pct"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise CompositionRenderError(f"Bubble {b.get('bubble_id')} has invalid local coordinates") from exc
    left = _round_half_up(x_pct * Decimal(str(canvas_width)) / Decimal("100"))
    right = _round_half_up((x_pct + w_pct) * Decimal(str(canvas_width)) / Decimal("100"))
    top = slot_top + _round_half_up(y_pct * Decimal(str(slot_height)) / Decimal("100"))
    bottom = slot_top + _round_half_up((y_pct + h_pct) * Decimal(str(slot_height)) / Decimal("100"))
    if left < 0 or right > canvas_width or right <= left or top < slot_top or bottom > slot_bottom or bottom <= top:
        raise CompositionRenderError(f"Bubble {b.get('bubble_id')} projects outside owner slot: ({left}, {top}, {right}, {bottom})")
    return (left, top, right, bottom)


def artifact_path(project_dir: Path | str, artifact_id: str) -> Path:
    """Resolve content-addressed review artifact path."""
    if not isinstance(artifact_id, str) or not artifact_id.startswith("artifact-"):
        raise ValueError(f"Invalid artifact_id: {artifact_id!r}")
    hex_hash = artifact_id[len("artifact-"):]
    if not SHA256_HEX_RE.match(hex_hash):
        raise ValueError(f"Invalid artifact_id hash: {artifact_id!r}")
    return Path(project_dir) / "assets" / "review-artifacts" / f"{artifact_id}.png"


def wrap_text_lines(
    text: str,
    font: ImageFont.FreeTypeFont,
    content_width: int,
) -> list[str]:
    """Greedy paragraph and whitespace wrap, falling back to codepoint hard-wrap.
    
    Preserves explicit newlines.
    Fails if a single codepoint cannot fit inside content_width.
    """
    if not text:
        return []

    lines: list[str] = []
    paragraphs = text.split("\n")

    for p in paragraphs:
        if not p:
            lines.append("")
            continue
        words = p.split()
        if not words:
            # Paragraph contains only whitespace
            lines.append("")
            continue

        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}" if current_line else word
            cand_len = font.getlength(candidate)
            if cand_len <= content_width:
                current_line = candidate
            else:
                # Need wrap. If current_line is not empty, commit it first and try word on fresh line
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                # Check if word fits on its own
                if font.getlength(word) <= content_width:
                    current_line = word
                else:
                    # Word exceeds line width: codepoint hard-wrap
                    sub_line = ""
                    for ch in word:
                        ch_len = font.getlength(ch)
                        if ch_len > content_width:
                            raise TypographyError(f"Codepoint {ch!r} width ({ch_len}) exceeds content width ({content_width})")
                        cand_sub = sub_line + ch
                        if font.getlength(cand_sub) <= content_width:
                            sub_line = cand_sub
                        else:
                            if sub_line:
                                lines.append(sub_line)
                            sub_line = ch
                    if sub_line:
                        current_line = sub_line

        if current_line:
            lines.append(current_line)

    return lines


def render_canonical(
    state: dict[str, Any],
    composition_revision: int,
    cuts: list[dict[str, Any]],
    font_bytes: bytes,
    ordered_cut_ids: Sequence[int] | None = None,
) -> RenderedArtifactBytes:
    """Render a v2 composition using its resolved integer slot layout and contain fit."""
    if isinstance(composition_revision, bool) or not isinstance(composition_revision, int) or composition_revision <= 0:
        raise CompositionValidationError(f"composition_revision must be a positive integer, got {composition_revision!r}")
    if not isinstance(cuts, list) or not cuts:
        raise CompositionRenderError("cuts must be a non-empty list")

    cut_payload_ids = [c.get("cut_id") for c in cuts if isinstance(c, dict)]
    if (
        len(cut_payload_ids) != len(cuts)
        or any(isinstance(cid, bool) or not isinstance(cid, int) or cid < 1 for cid in cut_payload_ids)
        or len(set(cut_payload_ids)) != len(cut_payload_ids)
    ):
        raise CompositionRenderError("cuts must contain unique positive cut IDs")
    if ordered_cut_ids is None:
        ordered_cut_ids = cut_payload_ids
    elif list(ordered_cut_ids) != cut_payload_ids:
        raise CompositionRenderError("cuts are not in the supplied ordered active cut set")

    norm_state = normalize_state(state, ordered_cut_ids)
    if len(norm_state["slot_heights_px"]) != len(cuts):
        raise CompositionRenderError(
            f"composition slot count {len(norm_state['slot_heights_px'])} does not match cuts ({len(cuts)})"
        )

    cut_closure: list[dict[str, Any]] = []
    decoded_cuts: list[Image.Image] = []
    for idx, c in enumerate(cuts):
        if not isinstance(c, dict):
            raise CompositionRenderError(f"cuts[{idx}] must be a dict")
        expected_cut_id = c.get("cut_id")
        if isinstance(expected_cut_id, bool) or not isinstance(expected_cut_id, int) or expected_cut_id < 1:
            raise CompositionRenderError(f"cuts[{idx}] cut_id must be a positive integer, got {expected_cut_id}")
        if idx > 0 and expected_cut_id in {item["cut_id"] for item in cut_closure}:
            raise CompositionRenderError(f"cuts contain duplicate cut_id {expected_cut_id}")
        cid = expected_cut_id
        d_rev = c.get("desired_revision")
        r_rev = c.get("realized_revision")
        if isinstance(d_rev, bool) or not isinstance(d_rev, int) or d_rev <= 0:
            raise CompositionRenderError(f"Cut {cid} desired_revision must be a positive integer, got {d_rev!r}")
        if isinstance(r_rev, bool) or not isinstance(r_rev, int) or r_rev <= 0:
            raise CompositionRenderError(f"Cut {cid} realized_revision must be a positive integer, got {r_rev!r}")
        if d_rev != r_rev:
            raise CompositionRenderError(f"Cut {cid} desired_revision ({d_rev}) != realized_revision ({r_rev})")
        asset_id = c.get("realized_asset_id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise CompositionRenderError(f"Cut {cid} realized_asset_id must be a non-empty string, got {asset_id!r}")
        expected_hash = c.get("realized_content_hash")
        if not isinstance(expected_hash, str) or not SHA256_HEX_RE.match(expected_hash):
            raise CompositionRenderError(f"Cut {cid} realized_content_hash must be 64-char lowercase hex sha256, got {expected_hash!r}")
        source_bytes = c.get("source_bytes")
        if not isinstance(source_bytes, (bytes, bytearray)) or len(source_bytes) == 0:
            raise SourceAssetError(f"Cut {cid} source_bytes is missing or empty")
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        if source_hash != expected_hash:
            raise SourceAssetError(f"Cut {cid} hash mismatch: expected {expected_hash}, got {source_hash}")
        try:
            img = Image.open(io.BytesIO(source_bytes))
            img.load()
            if img.format != "PNG" or img.width <= 0 or img.height <= 0:
                raise SourceAssetError(f"Cut {cid} source must be a non-empty PNG")
            decoded_cuts.append(img)
        except Exception as e:
            if isinstance(e, SourceAssetError):
                raise
            raise SourceAssetError(f"Cut {cid} failed to decode: {e}") from e
        cut_closure.append({
            "cut_id": cid,
            "display_order": idx + 1,
            "desired_revision": d_rev,
            "realized_revision": r_rev,
            "asset_id": asset_id,
            "source_content_hash": source_hash,
        })

    actual_font_hash = hashlib.sha256(font_bytes).hexdigest()
    if actual_font_hash != norm_state["font_sha256"]:
        raise TypographyError(
            f"Font hash mismatch: state specified {norm_state['font_sha256']}, font_bytes has {actual_font_hash}"
        )
    slots = compute_cut_slots(norm_state["slot_heights_px"], norm_state["gap_px"], ordered_cut_ids)
    canvas_height = slots[-1].bottom_px
    canvas = Image.new("RGBA", (CANONICAL_WIDTH, canvas_height), (255, 255, 255, 255))

    # Draw each source into its slot with centered contain semantics.
    for idx, img in enumerate(decoded_cuts):
        slot = slots[idx]
        slot_w = CANONICAL_WIDTH
        slot_h = slot.height_px
        scale_w = Decimal(str(slot_w)) / Decimal(str(img.width))
        scale_h = Decimal(str(slot_h)) / Decimal(str(img.height))
        scale = min(scale_w, scale_h)
        target_w = max(1, _round_half_up(Decimal(str(img.width)) * scale))
        target_h = max(1, _round_half_up(Decimal(str(img.height)) * scale))
        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if resized.mode != "RGBA":
            resized = resized.convert("RGBA")
        offset_x = (slot_w - target_w) // 2
        offset_y = slot.top_px + (slot_h - target_h) // 2
        canvas.alpha_composite(resized, (offset_x, offset_y))

    font_cache: dict[int, ImageFont.FreeTypeFont] = {}

    def get_font(size: int) -> ImageFont.FreeTypeFont:
        if size not in font_cache:
            try:
                font_cache[size] = ImageFont.truetype(
                    io.BytesIO(font_bytes), size=size, layout_engine=ImageFont.Layout.RAQM,
                )
            except Exception as e:
                raise TypographyError(f"Failed to initialize font at size {size} with RAQM: {e}") from e
        return font_cache[size]

    bubble_draw = ImageDraw.Draw(canvas, "RGBA")
    slots_by_cut = {slot.cut_id: slot for slot in slots}
    for b in norm_state["bubbles"]:
        if b["anchor_status"] != "ANCHORED":
            raise CompositionRenderError(f"Bubble {b.get('bubble_id')} requires manual re-anchoring")
        slot = slots_by_cut.get(b["cut_id"])
        if slot is None:
            raise CompositionRenderError(f"Bubble {b.get('bubble_id')} owner cut has no resolved slot")
        left, top, right, bottom = compute_bubble_geometry(b, slot, CANONICAL_WIDTH)
        box_w = right - left
        box_h = bottom - top
        fill_rgba = ImageColor.getcolor(b["fill_rgba"], "RGBA")
        outline_rgba = ImageColor.getcolor(b["outline_rgba"], "RGBA")
        text_rgba = ImageColor.getcolor(b["text_rgba"], "RGBA")
        outline_w_px = round_half_up(Decimal(str(b["outline_width_pct"])) * Decimal(str(CANONICAL_WIDTH)) / Decimal("100"))
        if b["shape"] == "ellipse":
            bubble_draw.ellipse((left, top, right - 1, bottom - 1), fill=fill_rgba, outline=outline_rgba if outline_w_px > 0 else None, width=outline_w_px)
        else:
            radius = round_half_up(Decimal(str(min(box_w, box_h))) / Decimal("8"))
            bubble_draw.rounded_rectangle((left, top, right - 1, bottom - 1), radius=radius, fill=fill_rgba, outline=outline_rgba if outline_w_px > 0 else None, width=outline_w_px)
        text = b["text"]
        if not text:
            continue
        font_size_px = round_half_up(Decimal(str(b["font_size_pct"])) * Decimal(str(CANONICAL_WIDTH)) / Decimal("100"))
        if font_size_px < 1:
            raise TypographyError(f"Bubble {b['bubble_id']} font_size_px < 1: {font_size_px}")
        font = get_font(font_size_px)
        min_dim = min(box_w, box_h)
        padding_px = round_half_up(Decimal(str(b["padding_pct"])) * Decimal(str(min_dim)) / Decimal("100"))
        content_left = left + padding_px + outline_w_px
        content_top = top + padding_px + outline_w_px
        content_right = right - padding_px - outline_w_px
        content_bottom = bottom - padding_px - outline_w_px
        content_w = content_right - content_left
        content_h = content_bottom - content_top
        if content_w <= 0 or content_h <= 0:
            raise TypographyError(f"Bubble {b['bubble_id']} padding/outline exceeds bubble area")
        lines = wrap_text_lines(text, font, content_w)
        if not lines:
            continue
        line_spacing_px = round_half_up(Decimal(str(b["line_spacing_pct"])) * Decimal(str(font_size_px)) / Decimal("100"))
        line_metrics: list[tuple[str, int, int]] = []
        total_text_height = 0
        ascent, descent = font.getmetrics()
        nominal_line_height = ascent + descent
        for idx, line in enumerate(lines):
            line_w = int(round(font.getlength(line)))
            line_metrics.append((line, line_w, nominal_line_height))
            total_text_height += nominal_line_height
            if idx > 0:
                total_text_height += line_spacing_px
        if total_text_height > content_h:
            raise TypographyError(f"Bubble {b['bubble_id']} text height ({total_text_height}px) overflows content height ({content_h}px)")
        cur_y = content_top + (content_h - total_text_height) // 2
        for line, line_w, line_height in line_metrics:
            if b["text_align"] == "left":
                cur_x = content_left
            elif b["text_align"] == "right":
                cur_x = content_right - line_w
            else:
                cur_x = content_left + (content_w - line_w) // 2
            bubble_draw.text((cur_x, cur_y), line, font=font, fill=text_rgba)
            cur_y += line_height + line_spacing_px

    final_rgb = Image.new("RGB", (CANONICAL_WIDTH, canvas_height), (255, 255, 255))
    final_rgb.paste(canvas, mask=canvas.split()[3])
    metadata_dict = {
        "contract": RENDERER_CONTRACT,
        "width_px": CANONICAL_WIDTH,
        "height_px": canvas_height,
        "gap_px": norm_state["gap_px"],
        "fit": norm_state["fit"],
        "slots": [slot.__dict__ for slot in slots],
        "state": norm_state,
        "composition_revision": composition_revision,
        "pillow_version": PIL.__version__,
        "font_sha256": actual_font_hash,
        "cuts": cut_closure,
    }
    metadata_json = canonical_json_dumps(metadata_dict)
    png_info = PngImagePlugin.PngInfo()
    png_info.add_text("comic_new_closure", metadata_json)
    out_bio = io.BytesIO()
    final_rgb.save(out_bio, format="PNG", optimize=False, compress_level=9, pnginfo=png_info)
    png_bytes = out_bio.getvalue()
    content_hash = hashlib.sha256(png_bytes).hexdigest()
    return RenderedArtifactBytes(
        png_bytes=png_bytes,
        content_hash=content_hash,
        artifact_id=f"artifact-{content_hash}",
        width=CANONICAL_WIDTH,
        height=canvas_height,
        composition_revision=composition_revision,
        closure=cut_closure,
        metadata_json=metadata_json,
    )

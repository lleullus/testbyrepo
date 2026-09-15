"""Canonical composition, geometry, PIL rendering, and deterministic PNG encoding for BLOCK-03."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFont, PngImagePlugin
import PIL

CANONICAL_WIDTH = 1024
CANONICAL_HEIGHT = 7680
TOTAL_CUTS = 5
SCHEMA_VERSION = 1
RENDERER_CONTRACT = "canonical-composition/v1"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{8}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


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


def normalize_color(val: Any, field_name: str) -> str:
    if not isinstance(val, str) or not HEX_COLOR_RE.match(val):
        raise CompositionValidationError(f"Field {field_name} must be #RRGGBBAA hex string, got {val!r}")
    return val.upper()


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Normalize composition state into the strict canonical schema v1.
    
    Rejects any unknown keys or invalid types/ranges.
    """
    if not isinstance(state, dict):
        raise CompositionValidationError(f"Composition state must be a dict, got {type(state)}")

    allowed_top_keys = {"schema_version", "gap_px", "font_sha256", "bubbles"}
    unknown_top = set(state.keys()) - allowed_top_keys
    if unknown_top:
        raise CompositionValidationError(f"Unknown top-level keys in state: {sorted(unknown_top)}")

    schema_version = state.get("schema_version")
    if schema_version != 1:
        raise CompositionValidationError(f"schema_version must be 1, got {schema_version!r}")

    gap_px = state.get("gap_px")
    if isinstance(gap_px, bool) or not isinstance(gap_px, int) or gap_px < 0:
        raise CompositionValidationError(f"gap_px must be a non-negative integer, got {gap_px!r}")

    usable_height = CANONICAL_HEIGHT - 4 * gap_px
    if usable_height < 5:
        raise CompositionValidationError(f"usable_height ({usable_height}) must be >= 5; gap_px {gap_px} is too large")

    font_sha256 = state.get("font_sha256")
    if not isinstance(font_sha256, str) or not SHA256_HEX_RE.match(font_sha256):
        raise CompositionValidationError(f"font_sha256 must be 64-character lowercase hex sha256, got {font_sha256!r}")
    bubbles_raw = state.get("bubbles")
    if not isinstance(bubbles_raw, list):
        raise CompositionValidationError(f"bubbles must be a list, got {type(bubbles_raw)}")

    normalized_bubbles: list[dict[str, Any]] = []
    seen_bubble_ids: set[str] = set()

    allowed_bubble_keys = {
        "bubble_id", "cut_id", "shape", "x_pct", "y_pct", "w_pct", "h_pct",
        "text", "font_size_pct", "line_spacing_pct", "text_align",
        "text_rgba", "fill_rgba", "outline_rgba", "outline_width_pct", "padding_pct"
    }

    for idx, b in enumerate(bubbles_raw):
        if not isinstance(b, dict):
            raise CompositionValidationError(f"Bubble at index {idx} must be a dict")
        unknown_b = set(b.keys()) - allowed_bubble_keys
        if unknown_b:
            raise CompositionValidationError(f"Unknown keys in bubble index {idx}: {sorted(unknown_b)}")

        bubble_id = b.get("bubble_id")
        if not isinstance(bubble_id, str) or not bubble_id.strip():
            raise CompositionValidationError(f"bubble_id at index {idx} must be non-empty string")
        if bubble_id in seen_bubble_ids:
            raise CompositionValidationError(f"Duplicate bubble_id {bubble_id!r} at index {idx}")
        seen_bubble_ids.add(bubble_id)

        cut_id = b.get("cut_id")
        if isinstance(cut_id, bool) or not isinstance(cut_id, int) or cut_id not in (1, 2, 3, 4, 5):
            raise CompositionValidationError(f"cut_id at index {idx} must be integer 1..5, got {cut_id!r}")

        shape = b.get("shape")
        if shape not in ("ellipse", "rounded_rectangle"):
            raise CompositionValidationError(f"shape at index {idx} must be 'ellipse' or 'rounded_rectangle', got {shape!r}")

        x_pct = normalize_percentage(b.get("x_pct"), f"bubbles[{idx}].x_pct", min_val=Decimal("0"), max_val=Decimal("100"))
        y_pct = normalize_percentage(b.get("y_pct"), f"bubbles[{idx}].y_pct", min_val=Decimal("0"), max_val=Decimal("100"))
        w_pct = normalize_percentage(b.get("w_pct"), f"bubbles[{idx}].w_pct", min_val=Decimal("0"), max_val=Decimal("100"), strictly_greater_than_min=True)
        h_pct = normalize_percentage(b.get("h_pct"), f"bubbles[{idx}].h_pct", min_val=Decimal("0"), max_val=Decimal("100"), strictly_greater_than_min=True)

        if Decimal(str(x_pct)) + Decimal(str(w_pct)) > Decimal("100"):
            raise CompositionValidationError(f"bubbles[{idx}] x_pct + w_pct ({x_pct} + {w_pct}) exceeds 100")
        if Decimal(str(y_pct)) + Decimal(str(h_pct)) > Decimal("100"):
            raise CompositionValidationError(f"bubbles[{idx}] y_pct + h_pct ({y_pct} + {h_pct}) exceeds 100")

        text = b.get("text")
        if not isinstance(text, str):
            raise CompositionValidationError(f"bubbles[{idx}].text must be string, got {type(text)}")

        font_size_pct = normalize_percentage(b.get("font_size_pct"), f"bubbles[{idx}].font_size_pct", min_val=Decimal("0"), max_val=Decimal("100"), strictly_greater_than_min=True)
        line_spacing_pct = normalize_percentage(b.get("line_spacing_pct"), f"bubbles[{idx}].line_spacing_pct", min_val=Decimal("0"), max_val=Decimal("500"))

        text_align = b.get("text_align")
        if text_align not in ("left", "center", "right"):
            raise CompositionValidationError(f"bubbles[{idx}].text_align must be 'left', 'center', or 'right', got {text_align!r}")

        text_rgba = normalize_color(b.get("text_rgba"), f"bubbles[{idx}].text_rgba")
        fill_rgba = normalize_color(b.get("fill_rgba"), f"bubbles[{idx}].fill_rgba")
        outline_rgba = normalize_color(b.get("outline_rgba"), f"bubbles[{idx}].outline_rgba")

        outline_width_pct = normalize_percentage(b.get("outline_width_pct"), f"bubbles[{idx}].outline_width_pct", min_val=Decimal("0"), max_val=Decimal("20"))
        padding_pct = normalize_percentage(b.get("padding_pct"), f"bubbles[{idx}].padding_pct", min_val=Decimal("0"), max_val=Decimal("50"), strictly_less_than_max=True)

        normalized_bubbles.append({
            "bubble_id": bubble_id,
            "cut_id": cut_id,
            "shape": shape,
            "x_pct": x_pct,
            "y_pct": y_pct,
            "w_pct": w_pct,
            "h_pct": h_pct,
            "text": text,
            "font_size_pct": font_size_pct,
            "line_spacing_pct": line_spacing_pct,
            "text_align": text_align,
            "text_rgba": text_rgba,
            "fill_rgba": fill_rgba,
            "outline_rgba": outline_rgba,
            "outline_width_pct": outline_width_pct,
            "padding_pct": padding_pct,
        })

    return {
        "schema_version": 1,
        "gap_px": gap_px,
        "font_sha256": font_sha256,
        "bubbles": normalized_bubbles,
    }


def canonical_json_dumps(obj: Any) -> str:
    """Deterministic, compact canonical JSON serialization."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_cut_slots(surface_height: int, gap_px: int) -> list[tuple[int, int]]:
    """Compute (y0, y1) slot boundaries for exactly 5 cuts using integer division.
    
    y0 = floor(i * usable_height / 5) + i * gap_px
    y1 = floor((i+1) * usable_height / 5) + i * gap_px
    """
    usable_height = surface_height - 4 * gap_px
    slots: list[tuple[int, int]] = []
    for i in range(5):
        y0 = (i * usable_height) // 5 + i * gap_px
        y1 = ((i + 1) * usable_height) // 5 + i * gap_px
        slots.append((y0, y1))
    return slots


def compute_bubble_geometry(b: dict[str, Any], surface_width: int, surface_height: int) -> tuple[int, int, int, int]:
    """Compute (left, top, right, bottom) pixel coordinates from percentage values.
    
    Uses Decimal half-up on each edge independently:
    left = round_half_up(x_pct * W / 100)
    top = round_half_up(y_pct * H / 100)
    right = round_half_up((x_pct + w_pct) * W / 100)
    bottom = round_half_up((y_pct + h_pct) * H / 100)
    """
    w_dec = Decimal(str(surface_width))
    h_dec = Decimal(str(surface_height))
    
    x_pct = Decimal(str(b["x_pct"]))
    y_pct = Decimal(str(b["y_pct"]))
    w_pct = Decimal(str(b["w_pct"]))
    h_pct = Decimal(str(b["h_pct"]))

    left = _round_half_up(x_pct * w_dec / Decimal("100"))
    top = _round_half_up(y_pct * h_dec / Decimal("100"))
    right = _round_half_up((x_pct + w_pct) * w_dec / Decimal("100"))
    bottom = _round_half_up((y_pct + h_pct) * h_dec / Decimal("100"))

    if right <= left or bottom <= top:
        raise CompositionRenderError(f"Bubble {b.get('bubble_id')} has non-positive area: ({left}, {top}, {right}, {bottom})")

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
) -> RenderedArtifactBytes:
    """Pure canonical renderer.
    
    Validates state, exact 5 cuts (order 1..5), source bytes/hashes,
    decodes images, draws slots and bubbles with text, and returns deterministic PNG bytes.
    """
    norm_state = normalize_state(state)

    if isinstance(composition_revision, bool) or not isinstance(composition_revision, int) or composition_revision <= 0:
        raise CompositionValidationError(f"composition_revision must be a positive integer, got {composition_revision!r}")

    if not isinstance(cuts, list) or len(cuts) != TOTAL_CUTS:
        raise CompositionRenderError(f"cuts must have exactly 5 items, got {len(cuts) if isinstance(cuts, list) else type(cuts)}")

    # Check cuts order 1..5 and validate each cut's strict fields
    cut_closure: list[dict[str, Any]] = []
    decoded_cuts: list[Image.Image] = []

    for idx, c in enumerate(cuts):
        if not isinstance(c, dict):
            raise CompositionRenderError(f"cuts[{idx}] must be a dict")
        expected_cut_id = idx + 1
        cid = c.get("cut_id")
        if cid != expected_cut_id:
            raise CompositionRenderError(f"cuts[{idx}] cut_id must be {expected_cut_id}, got {cid}")

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
            bio = io.BytesIO(source_bytes)
            img = Image.open(bio)
            img.load()
            if img.format not in ("PNG",):
                raise SourceAssetError(f"Cut {cid} format must be PNG, got {img.format}")
            if img.width <= 0 or img.height <= 0:
                raise SourceAssetError(f"Cut {cid} has non-positive dimensions ({img.width}x{img.height})")
            decoded_cuts.append(img)
        except Exception as e:
            if isinstance(e, SourceAssetError):
                raise
            raise SourceAssetError(f"Cut {cid} failed to decode: {e}") from e

        cut_closure.append({
            "cut_id": cid,
            "desired_revision": d_rev,
            "realized_revision": r_rev,
            "asset_id": asset_id,
            "source_content_hash": source_hash,
        })

    # Check font hash
    actual_font_hash = hashlib.sha256(font_bytes).hexdigest()
    if actual_font_hash != norm_state["font_sha256"]:
        raise TypographyError(
            f"Font hash mismatch: state specified {norm_state['font_sha256']}, font_bytes has {actual_font_hash}"
        )
    # Create canonical RGBA canvas
    canvas = Image.new("RGBA", (CANONICAL_WIDTH, CANONICAL_HEIGHT), (255, 255, 255, 255))
    slots = compute_cut_slots(CANONICAL_HEIGHT, norm_state["gap_px"])

    # 1. Draw cut images in their slots (contain)
    for idx, img in enumerate(decoded_cuts):
        y0, y1 = slots[idx]
        slot_w = CANONICAL_WIDTH
        slot_h = y1 - y0

        # Calculate contain scale
        scale_w = Decimal(str(slot_w)) / Decimal(str(img.width))
        scale_h = Decimal(str(slot_h)) / Decimal(str(img.height))
        scale = min(scale_w, scale_h)

        target_w = _round_half_up(Decimal(str(img.width)) * scale)
        target_h = _round_half_up(Decimal(str(img.height)) * scale)
        target_w = max(1, target_w)
        target_h = max(1, target_h)

        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if resized.mode != "RGBA":
            resized = resized.convert("RGBA")

        # Center in slot; odd remainder 1px placed right/bottom
        offset_x = (slot_w - target_w) // 2
        offset_y = y0 + (slot_h - target_h) // 2

        canvas.alpha_composite(resized, (offset_x, offset_y))

    # Font cache by size
    font_cache: dict[int, ImageFont.FreeTypeFont] = {}

    def get_font(size: int) -> ImageFont.FreeTypeFont:
        if size not in font_cache:
            try:
                font_cache[size] = ImageFont.truetype(
                    io.BytesIO(font_bytes),
                    size=size,
                    layout_engine=ImageFont.Layout.RAQM,
                )
            except Exception as e:
                raise TypographyError(f"Failed to initialize font at size {size} with RAQM: {e}") from e
        return font_cache[size]

    # 2. Draw bubbles and text
    bubble_draw = ImageDraw.Draw(canvas, "RGBA")

    for b in norm_state["bubbles"]:
        left, top, right, bottom = compute_bubble_geometry(b, CANONICAL_WIDTH, CANONICAL_HEIGHT)
        box_w = right - left
        box_h = bottom - top

        fill_rgba = ImageColor.getcolor(b["fill_rgba"], "RGBA")
        outline_rgba = ImageColor.getcolor(b["outline_rgba"], "RGBA")
        text_rgba = ImageColor.getcolor(b["text_rgba"], "RGBA")

        outline_w_px = round_half_up(Decimal(str(b["outline_width_pct"])) * Decimal(str(CANONICAL_WIDTH)) / Decimal("100"))
        
        # Draw bubble shape
        shape = b["shape"]
        if shape == "ellipse":
            bubble_draw.ellipse(
                (left, top, right - 1, bottom - 1),
                fill=fill_rgba,
                outline=outline_rgba if outline_w_px > 0 else None,
                width=outline_w_px,
            )
        elif shape == "rounded_rectangle":
            radius = round_half_up(Decimal(str(min(box_w, box_h))) / Decimal("8"))
            bubble_draw.rounded_rectangle(
                (left, top, right - 1, bottom - 1),
                radius=radius,
                fill=fill_rgba,
                outline=outline_rgba if outline_w_px > 0 else None,
                width=outline_w_px,
            )

        # Typography & Text
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

        # Measure line heights using getbbox
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
            raise TypographyError(
                f"Bubble {b['bubble_id']} text height ({total_text_height}px) overflows content height ({content_h}px)"
            )

        # Center text block vertically inside content box
        start_y = content_top + (content_h - total_text_height) // 2

        cur_y = start_y
        for idx, (line, line_w, l_height) in enumerate(line_metrics):
            if b["text_align"] == "left":
                cur_x = content_left
            elif b["text_align"] == "right":
                cur_x = content_right - line_w
            else:  # center
                cur_x = content_left + (content_w - line_w) // 2

            bubble_draw.text((cur_x, cur_y), line, font=font, fill=text_rgba)
            cur_y += l_height + line_spacing_px

    # Convert to opaque RGB
    final_rgb = Image.new("RGB", (CANONICAL_WIDTH, CANONICAL_HEIGHT), (255, 255, 255))
    final_rgb.paste(canvas, mask=canvas.split()[3])

    # Build deterministic closure metadata
    metadata_dict = {
        "contract": RENDERER_CONTRACT,
        "width": CANONICAL_WIDTH,
        "height": CANONICAL_HEIGHT,
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
    final_rgb.save(
        out_bio,
        format="PNG",
        optimize=False,
        compress_level=9,
        pnginfo=png_info,
    )
    png_bytes = out_bio.getvalue()
    content_hash = hashlib.sha256(png_bytes).hexdigest()
    art_id = f"artifact-{content_hash}"

    return RenderedArtifactBytes(
        png_bytes=png_bytes,
        content_hash=content_hash,
        artifact_id=art_id,
        width=CANONICAL_WIDTH,
        height=CANONICAL_HEIGHT,
        composition_revision=composition_revision,
        closure=cut_closure,
        metadata_json=metadata_json,
    )

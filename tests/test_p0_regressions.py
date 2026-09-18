from __future__ import annotations

import pytest

from comic_new.composition import CompositionValidationError, normalize_state


def _composition_with_bubble(cut_id: int) -> dict[str, object]:
    return {
        "schema_version": 2,
        "canvas_width_px": 1024,
        "gap_px": 24,
        "slot_heights_px": [1000, 1200],
        "fit": "contain",
        "font_sha256": "0" * 64,
        "bubbles": [
            {
                "anchor_status": "ANCHORED",
                "bubble_id": "bubble-stable-owner",
                "cut_id": cut_id,
                "shape": "rounded_rectangle",
                "local_x_pct": 10,
                "local_y_pct": 10,
                "local_w_pct": 40,
                "local_h_pct": 20,
                "text": "stable owner",
                "font_size_pct": 2,
                "line_spacing_pct": 20,
                "text_align": "center",
                "text_rgba": "#000000FF",
                "fill_rgba": "#FFFFFFFF",
                "outline_rgba": "#17191DFF",
                "outline_width_pct": 0.2,
                "padding_pct": 5,
            }
        ],
    }


def test_stable_cut_id_is_not_interpreted_as_a_slot_index() -> None:
    state = _composition_with_bubble(7)

    normalized = normalize_state(state)

    assert normalized["bubbles"][0]["cut_id"] == 7


def test_bubble_owner_is_validated_against_ordered_active_membership() -> None:
    state = _composition_with_bubble(7)

    normalized = normalize_state(state, ordered_cut_ids=[2, 7])
    assert normalized["bubbles"][0]["cut_id"] == 7

    with pytest.raises(CompositionValidationError, match="ordered active cut set"):
        normalize_state(state, ordered_cut_ids=[2, 3])

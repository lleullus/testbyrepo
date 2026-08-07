from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "project-shaper"
    / "skills"
    / "project-shaper"
    / "tools"
    / "validate_project_map.py"
)
SPEC = importlib.util.spec_from_file_location("validate_project_map", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def map_text(project: Path, slug: str) -> str:
    return f"""# Booking Platform

Status: approved
Owner: owner
Project-Root: {project}
Initiative-Slug: {slug}

## Product Outcome

Booking works.

## Product Boundary

Booking only.

## Reference Interpretation

Evidence only.

## MVP Cut

- WP-001

Complete booking.

## Work Packages

### WP-001: Reservation

Package-Status: deferred
Matt-Brief: None

#### Outcome

Reservations work.

#### Includes

- Reservations

#### Excludes

- Payments

#### Depends On

None

#### Why This Is One Package

One outcome.

#### Why It Is Separate

Separate lifecycle.

#### Decisions Reserved For Matt

None

## Dependency Map

- WP-001: None

## Deferred Capabilities

- WP-001

## Initiative-Level Open Questions

None

## Matt Handoff Queue

None
"""


class ProjectShaperLocationTests(unittest.TestCase):
    def test_accepts_map_in_project_local_initiative_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            project = Path(raw).resolve()
            slug = "booking-platform"
            directory = project / "docs" / "planning" / "initiatives" / slug
            directory.mkdir(parents=True)
            project_map = directory / "PROJECT-MAP.md"
            project_map.write_text(map_text(project, slug), encoding="utf-8")
            report = validator.validate(project_map)
            self.assertFalse([item for item in report.errors if item.code == "map.location"])

    def test_rejects_external_map_location(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            project = Path(raw).resolve()
            project_map = project / "PROJECT-MAP.md"
            project_map.write_text(map_text(project, "booking-platform"), encoding="utf-8")
            report = validator.validate(project_map)
            self.assertTrue([item for item in report.errors if item.code == "map.location"])


if __name__ == "__main__":
    unittest.main()

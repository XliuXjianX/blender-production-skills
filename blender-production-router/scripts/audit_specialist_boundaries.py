#!/usr/bin/env python3
"""Audit ownership and system-choice boundaries across the Blender skill suite."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SUITE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = SUITE_ROOT / "suite_manifest.json"
ROUTER_NAME = "blender-production-router"
STATE_FILES = ("task_route.json", "stage_state.json", "production_analysis.json")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def audit() -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    manifest: dict[str, Any] = {}
    try:
        manifest = json.loads(_read(MANIFEST_PATH))
    except Exception as exc:
        failures.append(f"manifest cannot be read: {exc}")

    skill_dirs = sorted(
        path
        for path in SUITE_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    manifest_names = [str(item.get("name")) for item in manifest.get("skills", [])]
    actual_names = [path.name for path in skill_dirs]
    _check(
        manifest.get("discovery", {}).get("expected_skill_count") == len(skill_dirs),
        "manifest expected_skill_count does not match actual Skill folders",
        failures,
    )
    _check(
        set(manifest_names) == set(actual_names),
        "manifest Skill names do not match actual Skill folders",
        failures,
    )
    _check(
        manifest.get("entry_skill") == ROUTER_NAME,
        "manifest entry_skill is not the production Router",
        failures,
    )
    _check(
        sum("Sole authority" in str(item.get("role", "")) for item in manifest.get("skills", [])) == 1,
        "manifest must contain exactly one sole-authority role",
        failures,
    )

    router_dir = SUITE_ROOT / ROUTER_NAME
    router_skill = _read(router_dir / "SKILL.md") if (router_dir / "SKILL.md").is_file() else ""
    contract = router_dir / "references" / "system-choice-contract.md"
    native_contract = router_dir / "references" / "native-component-contract.md"
    _check("Sole State Authority" in router_skill, "Router lacks explicit sole state authority", failures)
    _check(contract.is_file(), "system-choice-contract.md is missing", failures)
    _check(native_contract.is_file(), "native-component-contract.md is missing", failures)
    contract_text = _read(contract) if contract.is_file() else ""
    native_text = _read(native_contract) if native_contract.is_file() else ""
    _check(
        "native_boolean_required_for_normal_hard_surface_cuts" in contract_text,
        "system-choice contract lacks native Boolean exception",
        failures,
    )
    _check(
        "field-driven" in contract_text and "adaptive" in contract_text and "node_candidate" in contract_text,
        "system-choice contract lacks node escalation and comparison evidence",
        failures,
    )
    _check(
        bool(re.search(r"not\s+(?:a\s+)?last[-\s]resort\s+system", native_text, re.IGNORECASE)),
        "native component contract still presents Geometry Nodes as a last resort",
        failures,
    )

    for skill_dir in skill_dirs:
        text = _read(skill_dir / "SKILL.md")
        if skill_dir.name == ROUTER_NAME:
            continue
        has_authority_boundary = bool(
            re.search(
                r"(?:Router|blender-production-router).{0,140}?(?:owns|only.{0,60}authority|authority)",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
        ) or "Sole State Authority" in text
        _check(has_authority_boundary, f"{skill_dir.name} lacks a Router authority boundary", failures)

    stale_explicit_only = re.compile(
        r"geometry nodes\s+(?:only\s+)?when\s+(?:the\s+)?user\s+explicitly|only\s+use\s+geometry nodes\s+when\s+the\s+user",
        re.IGNORECASE,
    )
    for path in SUITE_ROOT.rglob("*.md"):
        if stale_explicit_only.search(_read(path)):
            failures.append(f"obsolete explicit-request-only Geometry Nodes rule: {path}")

    non_router_writers: list[str] = []
    write_pattern = re.compile(
        r"(?:" + "|".join(re.escape(name) for name in STATE_FILES) + r").*(?:write_text|json\.dump|rename|replace|unlink)|(?:write_text|json\.dump|rename|replace|unlink).*(?:" + "|".join(re.escape(name) for name in STATE_FILES) + r")",
        re.IGNORECASE,
    )
    for path in SUITE_ROOT.rglob("*.py"):
        if ROUTER_NAME in path.parts:
            continue
        try:
            text = _read(path)
        except OSError:
            continue
        if any(write_pattern.search(line) for line in text.splitlines()):
            non_router_writers.append(str(path))
    _check(
        not non_router_writers,
        "non-Router Python files appear to write production state: " + ", ".join(non_router_writers),
        failures,
    )

    asset_skill = SUITE_ROOT / "blender-local-asset-library"
    asset_text = _read(asset_skill / "SKILL.md") if (asset_skill / "SKILL.md").is_file() else ""
    _check("read-only" in asset_text.lower(), "local asset Skill is not explicitly read-only", failures)
    _check("does not own a production" in asset_text.lower(), "local asset Skill lacks scope boundary", failures)
    for path in (asset_skill / "scripts").glob("*.py") if (asset_skill / "scripts").is_dir() else []:
        source = _read(path)
        _check("bpy.ops.wm.save_as_mainfile" not in source, f"asset inspector may save source file: {path}", failures)
        _check(
            "bpy.ops.wm.append" not in source
            and "bpy.ops.wm.link" not in source
            and "bpy.data.libraries.load" not in source,
            f"asset inspector may import source data: {path}",
            failures,
        )

    if non_router_writers:
        warnings.append("Review the listed files before accepting a second state writer.")
    return {
        "schema_version": "1.0",
        "status": "PASS" if not failures else "FAIL",
        "suite_root": str(SUITE_ROOT),
        "skill_count": len(skill_dirs),
        "skills": actual_names,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = audit()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the runtime-probe fields in an enriched local asset capability catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _result(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = list(catalog.get("assets", []))
    tests: list[dict[str, Any]] = []

    runtime_fields = all("runtime_probe" in asset for asset in assets)
    tests.append(_result("runtime_probe_present", runtime_fields, f"{len(assets)} assets inspected."))

    inspected = [asset for asset in assets if asset.get("inspection_status") == "inspected"]
    inspected_failures = [
        asset
        for asset in inspected
        if asset.get("runtime_probe", {}).get("status") != "passed"
    ]
    tests.append(
        _result(
            "all_inspected_assets_runtime_callable",
            not inspected_failures,
            f"{len(inspected) - len(inspected_failures)}/{len(inspected)} passed; failures: "
            + ", ".join(str(asset.get("name")) for asset in inspected_failures[:8]),
        )
    )

    unavailable = [asset for asset in assets if asset.get("inspection_status") == "source_unavailable"]
    unavailable_honest = bool(unavailable) and all(
        asset.get("runtime_probe", {}).get("status") == "source_unavailable"
        and not asset.get("runtime_probe", {}).get("runtime_callable")
        for asset in unavailable
    )
    tests.append(
        _result(
            "unavailable_sources_remain_excluded",
            unavailable_honest,
            f"{len(unavailable)} source-unavailable assets retained as exclusions.",
        )
    )

    geometry = [
        asset
        for asset in inspected
        if str(asset.get("catalog", "")).startswith("Geometry Node")
    ]
    modes = {
        mode
        for asset in geometry
        for mode in asset.get("runtime_probe", {}).get("integration_modes", [])
    }
    tests.append(
        _result(
            "geometry_node_modes_are_distinguished",
            "modifier" in modes and "nested_group" in modes,
            "Observed Geometry Nodes integration modes: " + ", ".join(sorted(modes)),
        )
    )

    task_validation_required = all(
        bool(asset.get("runtime_probe", {}).get("task_scene_validation_required"))
        for asset in inspected
    )
    tests.append(
        _result(
            "runtime_probe_does_not_claim_task_scene_success",
            task_validation_required,
            "All runtime-callable assets still require task-scene validation.",
        )
    )

    source_reports = catalog.get("runtime_probe_sources", [])
    source_reports_compact = all(
        "node_groups" not in source and "objects" not in source
        for source in source_reports
    )
    tests.append(
        _result(
            "catalog_keeps_source_reports_compact",
            source_reports_compact,
            f"{len(source_reports)} source reports reference detailed sidecar JSON files.",
        )
    )

    output = {
        "schema_version": "1.0",
        "passed": all(test["passed"] for test in tests),
        "test_count": len(tests),
        "tests": tests,
    }
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=True))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

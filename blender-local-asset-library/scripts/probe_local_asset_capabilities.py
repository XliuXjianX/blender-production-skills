#!/usr/bin/env python3
"""Run isolated Blender runtime probes and merge evidence into a capability catalog.

The source library is opened only in background mode and is never saved.  The output catalog is
a cache artifact: it records that the current Blender runtime can instantiate each inspected data
block, not that every asset is automatically the right artistic or technical choice.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any

from search_local_asset_library import resolve_library_root, source_file_status


SCRIPT_DIR = Path(__file__).resolve().parent
BLENDER_PROBE = SCRIPT_DIR / "probe_local_asset_blend.py"

KIND_BY_ID_TYPE = {
    "NODETREE": "node_groups",
    "OBJECT": "objects",
    "MATERIAL": "materials",
    "COLLECTION": "collections",
}


def _run_source_probe(
    blender: Path,
    root: Path,
    source_rel: str,
    work_dir: Path,
) -> dict[str, Any]:
    source = root / source_rel
    report_path = work_dir / (source_rel.replace("/", "__").replace("\\", "__") + ".json")
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        str(source),
        "--python",
        str(BLENDER_PROBE),
        "--",
        str(report_path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    record: dict[str, Any] = {
        "source_blend": source_rel,
        "status": "failed",
        "returncode": completed.returncode,
        "report_path": str(report_path),
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }
    if completed.returncode != 0 or not report_path.is_file():
        return record
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        record["status"] = "invalid_report"
        record["error"] = str(exc)
        return record
    record.update(
        {
            "status": "probed",
            "blender_version": payload.get("blender_version"),
            "node_groups": payload.get("node_groups", []),
            "objects": payload.get("objects", []),
            "materials": payload.get("materials", []),
            "collections": payload.get("collections", []),
            "limitations": payload.get("limitations", []),
        }
    )
    return record


def _records_by_kind(source_probe: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    indexed: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for kind in ("node_groups", "objects", "materials", "collections"):
        by_name: dict[str, list[dict[str, Any]]] = {}
        for entry in source_probe.get(kind, []):
            by_name.setdefault(str(entry.get("name", "")), []).append(entry)
        indexed[kind] = by_name
    return indexed


def _compatibility_warning(inspection: dict[str, Any] | None) -> str | None:
    if not inspection:
        return None
    text = "\n".join(
        str(inspection.get(key, ""))
        for key in ("stdout_tail", "stderr_tail")
    ).lower()
    if "written by newer blender binary" in text or "expect loss of data" in text:
        return "Source was written by a newer Blender binary; it evaluated in this runtime but requires task-scene confirmation before use."
    return None


def _summarize_asset_probe(
    asset: dict[str, Any],
    source_probes: dict[str, dict[str, Any]],
    source_inspections: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_blends = [str(item) for item in asset.get("source_blends", [])]
    if asset.get("inspection_status") == "source_unavailable":
        return {
            "status": "source_unavailable",
            "runtime_callable": False,
            "reason": "The source .blend is missing or still a Git LFS pointer.",
            "task_scene_validation_required": True,
        }
    kind = KIND_BY_ID_TYPE.get(str(asset.get("id_type", "")).upper())
    if kind is None:
        return {
            "status": "unsupported_id_type",
            "runtime_callable": False,
            "reason": f"No runtime probe handler exists for Blender ID type {asset.get('id_type')!r}.",
            "task_scene_validation_required": True,
        }

    evidence: list[dict[str, Any]] = []
    missing_sources: list[str] = []
    for source in source_blends:
        source_probe = source_probes.get(source)
        if source_probe is None or source_probe.get("status") != "probed":
            missing_sources.append(source)
            continue
        records = _records_by_kind(source_probe).get(kind, {}).get(str(asset.get("name", "")), [])
        for record in records:
            probe = dict(record.get("probe", {}))
            evidence.append(
                {
                    "source_blend": source,
                    "data_block_kind": kind[:-1] if kind.endswith("s") else kind,
                    "probe": probe,
                    "compatibility_warning": _compatibility_warning(source_inspections.get(source)),
                }
            )
    statuses = [str(item.get("probe", {}).get("status", "failed")) for item in evidence]
    if not evidence:
        status = "source_probe_failed" if missing_sources else "data_block_not_found"
    elif any(value == "failed" for value in statuses):
        status = "failed"
    elif any(value == "warning" for value in statuses):
        status = "warning"
    elif all(value == "passed" for value in statuses):
        status = "passed"
    else:
        status = "inconclusive"
    integration_modes = sorted(
        {
            str(item.get("probe", {}).get("integration_mode"))
            for item in evidence
            if item.get("probe", {}).get("integration_mode")
        }
    )
    return {
        "status": status,
        "runtime_callable": status == "passed",
        "data_block_kind": kind[:-1] if kind.endswith("s") else kind,
        "integration_modes": integration_modes,
        "source_probe_missing": missing_sources,
        "evidence": evidence,
        "task_scene_validation_required": True,
        "semantic_validation_required": True,
        "meaning": (
            "Passing confirms isolated runtime instantiation in the recorded Blender version. "
            "It does not certify every input combination, external media, visual intent, performance, or production-scene compatibility."
        ),
    }


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temporary.replace(path)


def _compact_source_probe(source_probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_blend": source_probe.get("source_blend"),
        "status": source_probe.get("status"),
        "returncode": source_probe.get("returncode"),
        "report_path": source_probe.get("report_path"),
        "blender_version": source_probe.get("blender_version"),
        "source_status": source_probe.get("source_status"),
        "error": source_probe.get("error"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, help="Previously built inspected capability catalog JSON")
    parser.add_argument("--blender", required=True, help="Absolute Blender executable path")
    parser.add_argument("--output", required=True, help="Merged capability catalog JSON")
    parser.add_argument("--root", help="Asset library root or parent directory")
    parser.add_argument("--work-dir", help="Directory for per-source runtime probe reports")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when an inspected asset lacks a passing runtime probe")
    args = parser.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    blender = Path(args.blender).expanduser().resolve()
    if not catalog_path.is_file():
        raise SystemExit(f"Capability catalog not found: {catalog_path}")
    if not blender.is_file():
        raise SystemExit(f"Blender executable not found: {blender}")
    root = resolve_library_root(args.root)
    if root is None:
        raise SystemExit("Local Blender asset library was not found")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    work_dir = (
        Path(args.work_dir).expanduser().resolve()
        if args.work_dir
        else output_path.parent / "runtime-probes"
    )
    work_dir.mkdir(parents=True, exist_ok=True)

    source_paths = sorted(
        {
            source
            for asset in catalog.get("assets", [])
            for source in asset.get("source_blends", [])
        }
    )
    source_probes: dict[str, dict[str, Any]] = {}
    for source in source_paths:
        source_status = source_file_status(root, source)
        if not source_status.get("usable_source"):
            source_probes[source] = {
                "source_blend": source,
                "status": "source_unavailable",
                "source_status": source_status,
            }
            continue
        source_probes[source] = _run_source_probe(blender, root, source, work_dir)
        source_probes[source]["source_status"] = source_status

    source_inspections = {
        str(item.get("source_blend", "")): item
        for item in catalog.get("source_inspections", [])
    }
    result = dict(catalog)
    result["schema_version"] = "1.1"
    result["runtime_probe_generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    result["runtime_probe_blender_executable"] = str(blender)
    # Keep the detailed per-data-block reports in work_dir.  Repeating them in the catalog would
    # make every search load hundreds of irrelevant node descriptions.
    result["runtime_probe_sources"] = [
        _compact_source_probe(source_probes[source]) for source in source_paths
    ]
    result_assets: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for asset in catalog.get("assets", []):
        enriched = dict(asset)
        runtime_probe = _summarize_asset_probe(enriched, source_probes, source_inspections)
        enriched["runtime_probe"] = runtime_probe
        status = str(runtime_probe.get("status", "inconclusive"))
        status_counts[status] = status_counts.get(status, 0) + 1
        result_assets.append(enriched)
    result["assets"] = result_assets
    result["runtime_probe_summary"] = {
        "asset_status_counts": dict(sorted(status_counts.items())),
        "source_status_counts": {
            status: sum(1 for value in source_probes.values() if value.get("status") == status)
            for status in sorted({str(value.get("status")) for value in source_probes.values()})
        },
        "read_only_source_execution": True,
        "limitations": [
            "The source library is opened only in background Blender and is never saved.",
            "Runtime callable does not replace the owner Skill's task-scene integration and visual validation.",
        ],
    }
    _write_json_atomically(output_path, result)
    failure_count = sum(
        count
        for status, count in status_counts.items()
        if status not in {"passed", "source_unavailable"}
    )
    summary = {
        "status": "ok" if failure_count == 0 else "completed_with_failures",
        "output": str(output_path),
        "asset_status_counts": result["runtime_probe_summary"]["asset_status_counts"],
        "source_status_counts": result["runtime_probe_summary"]["source_status_counts"],
    }
    print(json.dumps(summary, ensure_ascii=True))
    return 1 if args.strict and failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create deterministic thumbnail overlay, difference image, and comparison metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat


def _mae(image: Image.Image) -> float:
    return sum(ImageStat.Stat(image).mean) / (len(image.getbands()) * 255.0)


def _crop_normalized(image: Image.Image, bbox: list[float]) -> Image.Image:
    x, y, width, height = bbox
    left = max(0, min(image.width - 1, round(x * image.width)))
    top = max(0, min(image.height - 1, round(y * image.height)))
    right = max(left + 1, min(image.width, round((x + width) * image.width)))
    bottom = max(top + 1, min(image.height, round((y + height) * image.height)))
    return image.crop((left, top, right, bottom))


def compare(
    reference: Path,
    render: Path,
    output_dir: Path,
    tag: str,
    observations: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    with Image.open(reference) as ref_source, Image.open(render) as render_source:
        ref = ref_source.convert("RGB")
        result = render_source.convert("RGB")
    ref_aspect = ref.width / max(ref.height, 1)
    render_aspect = result.width / max(result.height, 1)
    aspect_error = abs(render_aspect - ref_aspect) / max(ref_aspect, 1e-9)
    size = (256, max(1, round(256 / ref_aspect)))
    ref_thumb = ref.resize(size, Image.Resampling.LANCZOS)
    result_thumb = result.resize(size, Image.Resampling.LANCZOS)
    ref_gray = ImageOps.grayscale(ref_thumb)
    result_gray = ImageOps.grayscale(result_thumb)
    grayscale_mae = _mae(ImageChops.difference(ref_gray, result_gray))
    color_mae = _mae(ImageChops.difference(ref_thumb, result_thumb))
    ref_edges = ref_gray.filter(ImageFilter.FIND_EDGES)
    result_edges = result_gray.filter(ImageFilter.FIND_EDGES)
    edge_mae = _mae(ImageChops.difference(ref_edges, result_edges))
    grid_luminance_mae: list[float] = []
    for row in range(3):
        for column in range(4):
            box = [column / 4.0, row / 3.0, 1.0 / 4.0, 1.0 / 3.0]
            ref_region = _crop_normalized(ref_gray, box)
            result_region = _crop_normalized(result_gray, box)
            grid_luminance_mae.append(_mae(ImageChops.difference(ref_region, result_region)))
    p0_metrics: list[dict[str, object]] = []
    for observation in observations or []:
        if observation.get("priority") != "P0":
            continue
        bbox = observation.get("bbox_normalized")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        ref_region = _crop_normalized(ref_thumb, [float(value) for value in bbox])
        result_region = _crop_normalized(result_thumb, [float(value) for value in bbox])
        ref_region_gray = ImageOps.grayscale(ref_region)
        result_region_gray = ImageOps.grayscale(result_region)
        p0_metrics.append(
            {
                "id": observation.get("id"),
                "grayscale_mae": _mae(ImageChops.difference(ref_region_gray, result_region_gray)),
                "edge_mae": _mae(
                    ImageChops.difference(
                        ref_region_gray.filter(ImageFilter.FIND_EDGES),
                        result_region_gray.filter(ImageFilter.FIND_EDGES),
                    )
                ),
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = output_dir / f"reference_overlay_{tag}.png"
    difference_path = output_dir / f"reference_difference_{tag}.png"
    Image.blend(ref_thumb, result_thumb, 0.5).save(overlay_path)
    difference = ImageChops.difference(ref_thumb, result_thumb)
    difference.point(lambda value: min(255, value * 3)).save(difference_path)
    status = "PASS"
    max_grid_luminance_mae = max(grid_luminance_mae, default=0.0)
    max_p0_luminance_mae = max((float(item["grayscale_mae"]) for item in p0_metrics), default=0.0)
    max_p0_edge_mae = max((float(item["edge_mae"]) for item in p0_metrics), default=0.0)
    if (
        aspect_error > 0.01
        or grayscale_mae > 0.20
        or max_grid_luminance_mae > 0.32
        or max_p0_luminance_mae > 0.25
        or max_p0_edge_mae > 0.30
    ):
        status = "FAIL"
    elif (
        grayscale_mae > 0.12
        or edge_mae > 0.18
        or max_grid_luminance_mae > 0.18
        or max_p0_luminance_mae > 0.15
        or max_p0_edge_mae > 0.20
    ):
        status = "WARN"
    if not p0_metrics and status == "PASS":
        status = "WARN"
    return {
        "schema_version": "1.0",
        "status": status,
        "reference": str(reference),
        "render": str(render),
        "thumbnail_size": list(size),
        "aspect_ratio_error": aspect_error,
        "grayscale_mae": grayscale_mae,
        "color_mae": color_mae,
        "edge_mae": edge_mae,
        "grid_luminance_mae": grid_luminance_mae,
        "max_grid_luminance_mae": max_grid_luminance_mae,
        "p0_metrics": p0_metrics,
        "semantic_status": "REVIEW_REQUIRED" if p0_metrics else "P0_OBSERVATIONS_MISSING",
        "overlay": str(overlay_path),
        "difference": str(difference_path),
        "semantic_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--render", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output")
    parser.add_argument("--observation")
    args = parser.parse_args()
    observations = None
    if args.observation:
        observations = json.loads(Path(args.observation).expanduser().resolve().read_text(encoding="utf-8")).get("observations", [])
    report = compare(
        Path(args.reference).expanduser().resolve(),
        Path(args.render).expanduser().resolve(),
        Path(args.output_dir).expanduser().resolve(),
        args.tag,
        observations,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
